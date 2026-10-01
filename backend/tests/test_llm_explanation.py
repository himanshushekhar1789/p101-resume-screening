"""
Comprehensive test suite for Phase 10: LLM Explanations & Personalized Recommendations.

Validates:
1. Fully satisfied candidate (acknowledges strengths without inventing facts)
2. Missing skill (missing Phase 9 skill appears in key_gaps and requirement_explanations)
3. Insufficient skill (preserves quantitative shortfall e.g. 1.0 vs 3.0 years)
4. Not evaluable skill (uncertainty remains explicit; unverified tenure cited)
5. Semantic evidence cannot override deterministic status (MySQL vs PostgreSQL)
6. No hallucinated evidence (candidate without AWS cannot claim AWS experience)
7. Score preservation (preserves numerical score without alteration)
8. Recommendations only from gaps (Kubernetes gap -> Kubernetes recommendation only)
9. No hiring decision (no hire/reject/pass/fail structured fields)
10. Invalid LLM response (malformed JSON -> LLMValidationError / HTTP 422)
11. Mock provider deterministic offline execution (reproducible outputs)
12. REST API endpoint /api/v1/explanations/analyze
13. Integrated matching endpoint with include_explanation=True
14. Backward compatibility with include_explanation=False
15. File-based explanation endpoint /api/v1/explanations/from-files
"""

import os
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas import (
    CandidateProfile,
    PersonalInfo,
    SkillItem,
    ExperienceItem,
    EducationItem,
    JobProfile,
    JobSkillRequirement,
    JobExperienceRequirement,
    CandidateJobMatchResponse,
    CandidateJobScoreResponse,
    ScoreComponent,
    HybridScoreBreakdown,
    CandidateJobSkillGapResponse,

    SkillGapItem,
    ExperienceGapItem,
    SkillGapSummary,
    SkillGapStatus,
    LLMExplanationResponse,
    ExplanationAnalyzeRequest,
)
from backend.app.ai.llm_client import MockLLMClient
from backend.app.ai.validators import LLMValidationError
from backend.app.services.llm_explanation_service import (
    LLMExplanationService,
    generate_candidate_explanation,
)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Test 1 — Fully Satisfied Candidate
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fully_satisfied_candidate():
    """
    Candidate satisfies all job skills (Python, FastAPI, Docker).
    Verify explanation acknowledges satisfied requirements without inventing facts.
    """
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Alice Smith", email="alice@example.com"),
        skills=[
            SkillItem(name="Python", category="programming_language"),
            SkillItem(name="FastAPI", category="framework"),
            SkillItem(name="Docker", category="devops"),
        ],
        experience=[
            ExperienceItem(
                title="Senior Backend Engineer",
                company="TechCorp",
                start_date="2020-01",
                end_date="2024-01",
                skills=["Python", "FastAPI", "Docker"],
            )
        ],
    )
    job = JobProfile(
        job_title="Senior Backend Developer",
        skills=[
            JobSkillRequirement(name="Python", category="programming_language", priority="must_have", minimum_years=3.0),
            JobSkillRequirement(name="FastAPI", category="framework", priority="must_have"),
            JobSkillRequirement(name="Docker", category="devops", priority="nice_to_have"),
        ],
    )

    response = await generate_candidate_explanation(candidate=candidate, job=job)

    assert isinstance(response, LLMExplanationResponse)
    assert len(response.strengths) >= 2
    assert response.summary != ""
    assert "Python" in str(response.strengths)
    # No missing or insufficient gaps for this profile
    assert len(response.recommendations) == 0
    assert len(response.key_gaps) == 0


# ---------------------------------------------------------------------------
# Test 2 — Missing Skill
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_skill():
    """
    Job requires PostgreSQL, but candidate only possesses Python.
    Verify PostgreSQL appears as a missing gap with a grounded recommendation.
    """
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Bob Jones"),
        skills=[SkillItem(name="Python", category="programming_language")],
    )
    job = JobProfile(
        job_title="Backend Developer",
        skills=[
            JobSkillRequirement(name="Python", category="programming_language", priority="must_have"),
            JobSkillRequirement(name="PostgreSQL", category="database", priority="must_have"),
        ],
    )

    response = await generate_candidate_explanation(candidate=candidate, job=job)

    assert any("PostgreSQL" in gap for gap in response.key_gaps)
    # Check requirement explanations
    pg_explanations = [re for re in response.requirement_explanations if "PostgreSQL" in re.requirement_name]
    assert len(pg_explanations) == 1
    assert pg_explanations[0].status == "missing"
    assert "not directly demonstrated" in pg_explanations[0].explanation

    # Check recommendation
    pg_recs = [r for r in response.recommendations if "PostgreSQL" in r.skill]
    assert len(pg_recs) == 1
    assert pg_recs[0].gap_status == SkillGapStatus.MISSING
    assert "schema design" in pg_recs[0].recommendation or "PostgreSQL" in pg_recs[0].recommendation


# ---------------------------------------------------------------------------
# Test 3 — Insufficient Skill (Shortfall Preserved)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_insufficient_skill():
    """
    Job requires Docker with 3.0 years minimum experience.
    Candidate has Docker with 1.0 year verified experience.
    Verify explanation preserves the quantitative shortfall (2.0 years) and does not inflate tenure.
    """
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Charlie Davis"),
        skills=[SkillItem(name="Docker", category="devops")],
        experience=[
            ExperienceItem(
                title="Junior DevOps Engineer",
                company="StartupX",
                start_date="2023-01",
                end_date="2024-01",
                skills=["Docker"],
            )
        ],
    )
    job = JobProfile(
        job_title="DevOps Engineer",
        skills=[
            JobSkillRequirement(name="Docker", category="devops", priority="must_have", minimum_years=3.0)
        ],
    )

    response = await generate_candidate_explanation(candidate=candidate, job=job)

    docker_explanations = [re for re in response.requirement_explanations if "Docker" in re.requirement_name]
    assert len(docker_explanations) == 1
    assert docker_explanations[0].status == "insufficient"
    assert "1.0" in docker_explanations[0].explanation
    assert "3.0" in docker_explanations[0].explanation
    assert "2.0" in docker_explanations[0].explanation

    # Recommendation should cite insufficient experience
    docker_recs = [r for r in response.recommendations if "Docker" in r.skill]
    assert len(docker_recs) == 1
    assert docker_recs[0].gap_status == SkillGapStatus.INSUFFICIENT


# ---------------------------------------------------------------------------
# Test 4 — Not Evaluable Skill
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_not_evaluable_skill():
    """
    Candidate lists AWS in skills, but has 0 dated employment roles.
    Verify uncertainty remains explicit and unverified tenure is stated.
    """
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Dana White"),
        skills=[SkillItem(name="AWS", category="cloud")],
        experience=[],  # No dated experience
    )
    job = JobProfile(
        job_title="Cloud Engineer",
        skills=[
            JobSkillRequirement(name="AWS", category="cloud", priority="must_have", minimum_years=2.0)
        ],
    )

    response = await generate_candidate_explanation(candidate=candidate, job=job)

    aws_explanations = [re for re in response.requirement_explanations if "AWS" in re.requirement_name]
    assert len(aws_explanations) == 1
    assert aws_explanations[0].status == "not_evaluable"
    assert "does not establish verified tenure" in aws_explanations[0].explanation


# ---------------------------------------------------------------------------
# Test 5 — Semantic Evidence Cannot Override Deterministic Status
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_semantic_evidence_cannot_override_deterministic_status():
    """
    Job requires PostgreSQL. Candidate has MySQL (conceptually related, high cosine similarity).
    Verify explanation still states PostgreSQL is missing, and semantic evidence is cited purely as context.
    """
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Eve Black"),
        skills=[SkillItem(name="MySQL", category="database")],
    )
    job = JobProfile(
        job_title="Database Specialist",
        skills=[
            JobSkillRequirement(name="PostgreSQL", category="database", priority="must_have")
        ],
    )

    response = await generate_candidate_explanation(candidate=candidate, job=job, include_semantic=True)

    pg_explanations = [re for re in response.requirement_explanations if "PostgreSQL" in re.requirement_name]
    assert len(pg_explanations) == 1
    assert pg_explanations[0].status == "missing"
    # Semantic match is cited in explanation without overriding missing status
    assert "MySQL" in pg_explanations[0].explanation or "cannot substitute" in pg_explanations[0].explanation or "not directly demonstrated" in pg_explanations[0].explanation


# ---------------------------------------------------------------------------
# Test 6 — No Hallucinated Evidence
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_no_hallucinated_evidence():
    """
    Candidate profile contains no mention of AWS or Kubernetes.
    Verify generated output does not claim AWS or Kubernetes experience.
    """
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Frank Green"),
        skills=[SkillItem(name="Python", category="programming_language")],
    )
    job = JobProfile(
        job_title="Backend Developer",
        skills=[
            JobSkillRequirement(name="Python", category="programming_language"),
            JobSkillRequirement(name="Kubernetes", category="devops"),
        ],
    )

    response = await generate_candidate_explanation(candidate=candidate, job=job)

    # Strengths should NOT mention Kubernetes or AWS
    for strength in response.strengths:
        assert "Kubernetes" not in strength
        assert "AWS" not in strength


# ---------------------------------------------------------------------------
# Test 7 — Score Preservation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_score_preservation():
    """
    Provide explicit CandidateJobScoreResponse with fit score 0.72.
    Verify explanation layer explains the score without modifying numerical values.
    """
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Grace Hopper"),
        skills=[SkillItem(name="Python", category="programming_language")],
    )
    job = JobProfile(
        job_title="Software Engineer",
        skills=[
            JobSkillRequirement(name="Python", category="programming_language", priority="must_have"),
            JobSkillRequirement(name="Go", category="programming_language", priority="must_have"),
        ],
    )

    dummy_comp = ScoreComponent(
        name="test",
        score=0.8,
        configured_weight=0.3,
        effective_weight=0.3,
        weighted_contribution=0.24,
    )
    score_res = CandidateJobScoreResponse(
        candidate_fit_score=0.72,
        percentage_score=72.0,
        rule_fit_score=0.80,
        semantic_fit_score=0.74,
        experience_fit_score=0.60,
        components=HybridScoreBreakdown(
            rule_fit=dummy_comp,
            semantic_fit=dummy_comp,
            experience_fit=dummy_comp,
            llm_fit=dummy_comp,
        ),
        all_must_haves_satisfied=False,
        explanation="Test score explanation",
    )


    response = await generate_candidate_explanation(
        candidate=candidate,
        job=job,
        scoring_result=score_res,
    )

    assert response.score_explanation is not None
    assert "0.72" in response.score_explanation
    assert "0.80" in response.score_explanation
    assert "0.74" in response.score_explanation
    assert "0.60" in response.score_explanation


# ---------------------------------------------------------------------------
# Test 8 — Recommendations Only From Gaps
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_recommendations_only_from_gaps():
    """
    Candidate satisfies Python and FastAPI, but lacks Kubernetes.
    Verify recommendations strictly target Kubernetes and do NOT recommend unrelated technologies.
    """
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Henry Ford"),
        skills=[
            SkillItem(name="Python", category="programming_language"),
            SkillItem(name="FastAPI", category="framework"),
        ],
    )
    job = JobProfile(
        job_title="Backend Engineer",
        skills=[
            JobSkillRequirement(name="Python", category="programming_language", priority="must_have"),
            JobSkillRequirement(name="FastAPI", category="framework", priority="must_have"),
            JobSkillRequirement(name="Kubernetes", category="devops", priority="must_have"),
        ],
    )

    response = await generate_candidate_explanation(candidate=candidate, job=job)

    assert len(response.recommendations) == 1
    assert "Kubernetes" in response.recommendations[0].skill
    # Must NOT recommend AWS, React, etc.
    rec_text = response.recommendations[0].recommendation
    assert "React" not in rec_text
    assert "AWS" not in rec_text


# ---------------------------------------------------------------------------
# Test 9 — No Hiring Decision
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_no_hiring_decision():
    """
    Verify explanation contains no structured hiring or rejection decision fields.
    """
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Irene Adler"),
        skills=[SkillItem(name="Python", category="programming_language")],
    )
    job = JobProfile(
        job_title="Developer",
        skills=[JobSkillRequirement(name="Python", category="programming_language")],
    )

    response = await generate_candidate_explanation(candidate=candidate, job=job)

    # Inspect schema dump for forbidden keywords
    dump = response.model_dump()
    forbidden_keys = ["hire", "reject", "recommended_for_hire", "decision", "rank", "shortlist"]
    for key in forbidden_keys:
        assert key not in dump

    # Check disclaimer
    assert "does not constitute a hiring or rejection decision" in response.disclaimer


# ---------------------------------------------------------------------------
# Test 10 — Invalid LLM Response
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_invalid_llm_response():
    """
    Mock LLM returns malformed non-JSON string.
    Verify LLMValidationError is raised cleanly without crashing silently.
    """
    mock_client = MockLLMClient()
    mock_client.set_responses(["THIS IS NOT A VALID JSON OBJECT"])

    candidate = CandidateProfile(personal_info=PersonalInfo(name="Jack Vance"))
    job = JobProfile(job_title="Software Engineer")

    with pytest.raises(LLMValidationError):
        await generate_candidate_explanation(
            candidate=candidate,
            job=job,
            llm_client=mock_client,
        )


# ---------------------------------------------------------------------------
# Test 11 — Mock Provider Deterministic Offline
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_mock_provider_deterministic_offline():
    """
    Verify mock provider runs 100% offline and generates bitwise identical responses for repeated executions.
    """
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Karen Page"),
        skills=[SkillItem(name="Python", category="programming_language")],
    )
    job = JobProfile(
        job_title="Python Developer",
        skills=[
            JobSkillRequirement(name="Python", category="programming_language"),
            JobSkillRequirement(name="Django", category="framework"),
        ],
    )

    client1 = MockLLMClient()
    client2 = MockLLMClient()

    res1 = await generate_candidate_explanation(candidate=candidate, job=job, llm_client=client1)
    res2 = await generate_candidate_explanation(candidate=candidate, job=job, llm_client=client2)

    assert res1.summary == res2.summary
    assert res1.strengths == res2.strengths
    assert res1.key_gaps == res2.key_gaps
    assert len(res1.recommendations) == len(res2.recommendations)


# ---------------------------------------------------------------------------
# Test 12 — REST API Endpoint /api/v1/explanations/analyze
# ---------------------------------------------------------------------------
def test_api_explanations_analyze_endpoint(client):
    """
    Verify POST /api/v1/explanations/analyze returns HTTP 200 with complete LLMExplanationResponse.
    """
    payload = {
        "candidate": {
            "personal_info": {"name": "Leo Tolstoy", "email": "leo@example.com"},
            "skills": [
                {"name": "Python", "category": "programming_language"},
                {"name": "FastAPI", "category": "framework"},
            ],
        },
        "job": {
            "job_title": "Senior Backend Developer",
            "skills": [
                {"name": "Python", "category": "programming_language", "priority": "must_have"},
                {"name": "Docker", "category": "devops", "priority": "must_have"},
            ],
        },
        "candidate_id": "cand_12",
        "job_id": "job_12",
    }

    response = client.post("/api/v1/explanations/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["candidate_name"] == "Leo Tolstoy"
    assert data["job_title"] == "Senior Backend Developer"
    assert len(data["strengths"]) >= 1
    assert any("Docker" in gap for gap in data["key_gaps"])
    assert len(data["recommendations"]) == 1
    assert data["recommendations"][0]["skill"] == "Docker"
    assert "does not constitute a hiring or rejection decision" in data["disclaimer"]


# ---------------------------------------------------------------------------
# Test 13 — Integrated Endpoint with include_explanation=True
# ---------------------------------------------------------------------------
def test_integrated_endpoint_include_explanation_true(client):
    """
    Verify POST /api/v1/matching/analyze with include_explanation=True returns populated explanation field.
    """
    payload = {
        "candidate": {
            "personal_info": {"name": "Maya Angelou"},
            "skills": [{"name": "Python", "category": "programming_language"}],
        },
        "job": {
            "job_title": "Software Engineer",
            "skills": [
                {"name": "Python", "category": "programming_language", "priority": "must_have"},
                {"name": "Kubernetes", "category": "devops", "priority": "must_have"},
            ],
        },
        "include_explanation": True,
        "include_skill_gaps": True,
        "include_score": True,
    }

    response = client.post("/api/v1/matching/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["explanation"] is not None
    assert "summary" in data["explanation"]
    assert "recommendations" in data["explanation"]
    assert data["gaps"] is not None
    assert data["score"] is not None


# ---------------------------------------------------------------------------
# Test 14 — Backward Compatibility with include_explanation=False
# ---------------------------------------------------------------------------
def test_integrated_endpoint_backward_compatibility(client):
    """
    Verify POST /api/v1/matching/analyze with include_explanation=False (default) returns explanation=None.
    """
    payload = {
        "candidate": {
            "personal_info": {"name": "Nathan Drake"},
            "skills": [{"name": "Python", "category": "programming_language"}],
        },
        "job": {
            "job_title": "Backend Dev",
            "skills": [{"name": "Python", "category": "programming_language"}],
        },
        "include_explanation": False,
    }

    response = client.post("/api/v1/matching/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data.get("explanation") is None


# ---------------------------------------------------------------------------
# Test 15 — File-Based Explanation Endpoint /api/v1/explanations/from-files
# ---------------------------------------------------------------------------
def test_file_based_explanation_endpoint(client):
    """
    Verify POST /api/v1/explanations/from-files with real PDF/DOCX sample files.
    """
    resume_path = "data/sample/resumes/synthetic_software_engineer.pdf"
    job_path = "data/sample/job_descriptions/backend_engineer_jd.pdf"

    if not os.path.exists(resume_path) or not os.path.exists(job_path):
        pytest.skip("Sample PDF files not found for file-based test.")


    with open(resume_path, "rb") as rf, open(job_path, "rb") as jf:
        response = client.post(
            "/api/v1/explanations/from-files",
            files={
                "resume_file": ("synthetic_software_engineer.pdf", rf, "application/pdf"),
                "job_file": ("backend_developer_jd.pdf", jf, "application/pdf"),
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "strengths" in data
    assert "requirement_explanations" in data
    assert "disclaimer" in data
