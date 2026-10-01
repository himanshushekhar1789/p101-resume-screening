"""
Comprehensive test suite for Phase 9: Skill-Gap Analysis & Evidence Grounding.

Validates:
1. Perfect skill match (all satisfied, missing=0, insufficient=0)
2. Missing must-have skill (missing=1, must_have_gaps=1, empty candidate evidence)
3. Missing nice-to-have skill (missing=1, nice_to_have_gaps=1, must_have_gaps=0)
4. Insufficient skill-specific experience (tenure shortfall calculated accurately)
5. Not evaluable skill (skill present without dated role tenure, excluded from must_have_gaps)
6. Semantic similarity cannot override deterministic missing (Rule 6: PostgreSQL missing despite MySQL similarity)
7. General career experience remains strictly separate in experience_gaps (not in skill_gaps)
8. Evidence preservation (traceable quotes preserved, zero hallucinated evidence)
9. Duplicate normalized skills (aliases/variants like JS and JavaScript merged cleanly with must_have precedence)
10. Skill gap summary arithmetic invariants (counts, sums, must_have vs nice_to_have)
11. No ranking or hiring decision fields in response schema
12. REST API endpoint /api/v1/gaps/analyze
13. REST API endpoint /api/v1/gaps/from-files (PDF/DOCX end-to-end)
14. Unified matching API /api/v1/matching/analyze?include_skill_gaps=true
15. Unified matching API /api/v1/matching/from-files?include_skill_gaps=true
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
    MatchStatus,
    MatchMethod,
    SemanticStatus,
    SemanticMatchResult,
    RequirementReference,
    SingleRequirementMatch,
    CandidateJobMatchResponse,
    MatchingSummary,
    SkillGapStatus,
    SkillGapItem,
    ExperienceGapItem,
    SkillGapSummary,
    CandidateJobSkillGapResponse,
    SkillGapAnalyzeRequest,
)
from backend.app.services.skill_normalizer import (
    normalize_candidate_skills,
    normalize_job_skills,
)
from backend.app.services.skill_gap_analyzer import (
    SkillGapAnalyzer,
    get_skill_gap_analyzer,
    analyze_skill_gaps,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def analyzer():
    return SkillGapAnalyzer(current_year=2026.0)


# ---------------------------------------------------------------------------
# Test 1 — Perfect Skill Match
# ---------------------------------------------------------------------------
def test_perfect_skill_match(analyzer):
    """
    Candidate possesses all required skills (Python, FastAPI, Docker).
    All skill gaps must be marked SATISFIED; missing = 0, insufficient = 0, must_have_gaps = 0.
    """
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Alice Smith", email="alice@example.com"),
        skills=[
            SkillItem(name="Python", category="programming_language"),
            SkillItem(name="FastAPI", category="framework"),
            SkillItem(name="Docker", category="devops"),
        ],
    )
    job = JobProfile(
        job_title="Backend Developer",
        skills=[
            JobSkillRequirement(name="Python", category="programming_language", priority="must_have", evidence="Required: Python"),
            JobSkillRequirement(name="FastAPI", category="framework", priority="must_have", evidence="Required: FastAPI"),
            JobSkillRequirement(name="Docker", category="devops", priority="nice_to_have", evidence="Nice to have: Docker"),
        ],
    )

    response = analyzer.analyze(candidate=candidate, job=job)

    assert len(response.skill_gaps) == 3
    assert response.summary.total_skill_requirements == 3
    assert response.summary.satisfied_count == 3
    assert response.summary.missing_count == 0
    assert response.summary.insufficient_count == 0
    assert response.summary.not_evaluable_count == 0
    assert response.summary.must_have_gaps == 0
    assert response.summary.nice_to_have_gaps == 0
    assert response.summary.must_have_satisfied == 2
    assert response.summary.nice_to_have_satisfied == 1

    for gap in response.skill_gaps:
        assert gap.status == SkillGapStatus.SATISFIED
        assert gap.candidate_value is not None
        assert "satisfies skill requirement" in gap.explanation


# ---------------------------------------------------------------------------
# Test 2 — Missing Must-Have Skill
# ---------------------------------------------------------------------------
def test_missing_must_have_skill(analyzer):
    """
    JD: Python, FastAPI, Kubernetes (all must_have).
    Candidate has: Python, FastAPI (missing Kubernetes).
    Kubernetes must be marked MISSING with must_have priority, empty candidate evidence,
    and must_have_gaps must equal 1.
    """
    candidate = CandidateProfile(
        skills=[
            SkillItem(name="Python", category="programming_language"),
            SkillItem(name="FastAPI", category="framework"),
        ]
    )
    job = JobProfile(
        job_title="Cloud Engineer",
        skills=[
            JobSkillRequirement(name="Python", priority="must_have", evidence="5+ years Python required"),
            JobSkillRequirement(name="FastAPI", priority="must_have", evidence="FastAPI framework required"),
            JobSkillRequirement(name="Kubernetes", priority="must_have", evidence="Hands-on Kubernetes experience required"),
        ],
    )

    response = analyzer.analyze(candidate=candidate, job=job)

    assert response.summary.total_skill_requirements == 3
    assert response.summary.satisfied_count == 2
    assert response.summary.missing_count == 1
    assert response.summary.must_have_gaps == 1

    k8s_gap = next((g for g in response.skill_gaps if g.canonical_skill_name == "Kubernetes"), None)
    assert k8s_gap is not None
    assert k8s_gap.status == SkillGapStatus.MISSING
    assert k8s_gap.priority == "must_have"
    assert k8s_gap.candidate_evidence == []  # Rule 1: No invented candidate evidence
    assert any("Kubernetes" in ev for ev in k8s_gap.job_evidence)  # Rule 2: Grounded in JD
    assert "No verifiable candidate evidence found" in k8s_gap.explanation  # Rule 3


# ---------------------------------------------------------------------------
# Test 3 — Missing Nice-to-Have Skill
# ---------------------------------------------------------------------------
def test_missing_nice_to_have_skill(analyzer):
    """
    JD: Python (must_have), Terraform (nice_to_have).
    Candidate has: Python.
    Terraform must be marked MISSING with priority nice_to_have.
    Crucial: nice_to_have_gaps = 1, while must_have_gaps MUST remain 0.
    """
    candidate = CandidateProfile(
        skills=[SkillItem(name="Python", category="programming_language")]
    )
    job = JobProfile(
        skills=[
            JobSkillRequirement(name="Python", priority="must_have"),
            JobSkillRequirement(name="Terraform", priority="nice_to_have", evidence="Terraform is a plus"),
        ]
    )

    response = analyzer.analyze(candidate=candidate, job=job)

    assert response.summary.total_skill_requirements == 2
    assert response.summary.satisfied_count == 1
    assert response.summary.missing_count == 1
    assert response.summary.must_have_gaps == 0  # Not a mandatory gap!
    assert response.summary.nice_to_have_gaps == 1

    tf_gap = next(g for g in response.skill_gaps if g.canonical_skill_name == "Terraform")
    assert tf_gap.status == SkillGapStatus.MISSING
    assert tf_gap.priority == "nice_to_have"
    assert tf_gap.candidate_evidence == []


# ---------------------------------------------------------------------------
# Test 4 — Insufficient Skill-Specific Experience
# ---------------------------------------------------------------------------
def test_insufficient_skill_specific_experience(analyzer):
    """
    JD: 3.0 years of Python experience required.
    Candidate: Has Python, but only 1.0 year verified in dated work experience (2024-2025).
    Python must be marked INSUFFICIENT.
    Shortfall must be quantified: 3.0 - 1.0 = 2.0 years.
    """
    candidate = CandidateProfile(
        skills=[SkillItem(name="Python", category="programming_language")],
        experience=[
            ExperienceItem(
                title="Junior Python Developer",
                company="StartupCo",
                start_date="2024",
                end_date="2025",
                skills=["Python"],
                description="Built scripts using Python.",
            )
        ],
    )
    job = JobProfile(
        skills=[
            JobSkillRequirement(
                name="Python",
                category="programming_language",
                priority="must_have",
                minimum_years=3.0,
                evidence="3+ years of Python experience required",
            )
        ]
    )

    response = analyzer.analyze(candidate=candidate, job=job)

    assert response.summary.insufficient_count == 1
    assert response.summary.must_have_gaps == 1

    py_gap = response.skill_gaps[0]
    assert py_gap.status == SkillGapStatus.INSUFFICIENT
    assert py_gap.required_value == "3.0 years"
    assert "1.0 years" in py_gap.candidate_value
    assert py_gap.shortfall == "2.0 years"
    assert "falls short of the required 3.0 years by 2.0 years" in py_gap.explanation


# ---------------------------------------------------------------------------
# Test 5 — Not Evaluable Skill
# ---------------------------------------------------------------------------
def test_not_evaluable_skill(analyzer):
    """
    Candidate lists Python in skills section, but provides zero dated work experience roles.
    JD demands 3.0 years of Python.
    Status must be NOT_EVALUABLE.
    CRITICAL INVARIANT (Section 11): not_evaluable must NOT be counted in must_have_gaps!
    """
    candidate = CandidateProfile(
        skills=[SkillItem(name="Python", category="programming_language")],
        experience=[],  # No dated roles
    )
    job = JobProfile(
        skills=[
            JobSkillRequirement(
                name="Python",
                priority="must_have",
                minimum_years=3.0,
                evidence="3+ years Python required",
            )
        ]
    )

    response = analyzer.analyze(candidate=candidate, job=job)

    assert response.summary.total_skill_requirements == 1
    assert response.summary.not_evaluable_count == 1
    assert response.summary.must_have_gaps == 0  # Uncertainty != confirmed gap
    assert response.summary.missing_count == 0
    assert response.summary.insufficient_count == 0

    py_gap = response.skill_gaps[0]
    assert py_gap.status == SkillGapStatus.NOT_EVALUABLE
    assert "cannot be verified" in py_gap.explanation or "without speculation" in py_gap.explanation


# ---------------------------------------------------------------------------
# Test 6 — Semantic Similarity Cannot Override Deterministic Missing
# ---------------------------------------------------------------------------
def test_semantic_similarity_cannot_override_deterministic_missing(analyzer):
    """
    JD requires: PostgreSQL (must_have).
    Candidate has: MySQL (database).
    SentenceTransformers will report high cosine similarity between MySQL and PostgreSQL (~0.68).
    However, deterministic match is unmatched.
    RULE 6 MANDATE:
    PostgreSQL must remain status = MISSING. High semantic similarity must NOT make it satisfied or partial.
    Supporting semantic evidence must be noted in the explanation and semantic fields.
    """
    candidate = CandidateProfile(
        skills=[SkillItem(name="MySQL", category="database")],
    )
    job = JobProfile(
        skills=[
            JobSkillRequirement(name="PostgreSQL", category="database", priority="must_have", evidence="Required: PostgreSQL"),
        ]
    )

    response = analyzer.analyze(candidate=candidate, job=job, include_semantic=True)

    pg_gap = next(g for g in response.skill_gaps if g.canonical_skill_name == "PostgreSQL")
    assert pg_gap.status == SkillGapStatus.MISSING  # Invariant: NEVER overridden to satisfied!
    assert pg_gap.priority == "must_have"
    assert pg_gap.deterministic_match_status == MatchStatus.UNMATCHED
    assert response.summary.missing_count == 1
    assert response.summary.must_have_gaps == 1


# ---------------------------------------------------------------------------
# Test 7 — General Experience Remains Separate
# ---------------------------------------------------------------------------
def test_general_experience_remains_separate(analyzer):
    """
    JD:
    - Python (skill, must_have)
    - 5+ years backend software development (general experience, minimum_years=5.0)
    Candidate:
    - Python (skill)
    - 3.0 years backend development (2021-2024)
    SECTION 9 MANDATE:
    - Python is in skill_gaps (status = SATISFIED).
    - "backend" is NOT added as a skill gap!
    - General experience is placed in experience_gaps with shortfall_years = 2.0.
    """
    candidate = CandidateProfile(
        skills=[SkillItem(name="Python", category="programming_language")],
        experience=[
            ExperienceItem(
                title="Backend Software Engineer",
                company="TechCorp",
                start_date="2021",
                end_date="2024",
                skills=["Python"],
                description="Designed backend microservices.",
            )
        ],
    )
    job = JobProfile(
        skills=[
            JobSkillRequirement(name="Python", priority="must_have", evidence="Python required")
        ],
        experience_requirements=[
            JobExperienceRequirement(
                skill=None,  # General career tenure
                minimum_years=5.0,
                priority="must_have",
                text="5+ years of backend software engineering experience",
                evidence="5+ years backend software engineering required",
            )
        ],
    )

    response = analyzer.analyze(candidate=candidate, job=job)

    # 1. skill_gaps contains ONLY the skill
    assert len(response.skill_gaps) == 1
    assert response.skill_gaps[0].canonical_skill_name == "Python"
    assert response.skill_gaps[0].status == SkillGapStatus.SATISFIED
    assert not any("backend" in g.skill_name.lower() for g in response.skill_gaps)

    # 2. experience_gaps contains the career tenure requirement
    assert len(response.experience_gaps) == 1
    exp_gap = response.experience_gaps[0]
    assert exp_gap.status == SkillGapStatus.INSUFFICIENT
    assert exp_gap.required_years == 5.0
    assert exp_gap.candidate_years == 3.0
    assert exp_gap.shortfall_years == 2.0
    assert "falls short of required 5.0 years by 2.0 years" in exp_gap.explanation

    # 3. Summary reflects separation
    assert response.summary.total_skill_requirements == 1
    assert response.summary.must_have_gaps == 0
    assert response.summary.total_experience_requirements == 1
    assert response.summary.experience_gaps_count == 1


# ---------------------------------------------------------------------------
# Test 8 — Evidence Preservation
# ---------------------------------------------------------------------------
def test_evidence_preservation(analyzer):
    """
    Verifies that all gaps contain grounded, non-hallucinated evidence:
    - Matched skill: quotes actual candidate experience/skills.
    - Missing skill: candidate_evidence is strictly [] (empty).
    - Job evidence: quotes verbatim requirement text.
    """
    candidate = CandidateProfile(
        skills=[SkillItem(name="Python", category="programming_language")],
        experience=[
            ExperienceItem(
                title="Lead Python Architect",
                company="DataSystems",
                start_date="2020",
                end_date="2025",
                skills=["Python"],
                description="Engineered high-throughput pipelines.",
            )
        ],
    )
    job = JobProfile(
        skills=[
            JobSkillRequirement(name="Python", priority="must_have", evidence="Must have Python expertise"),
            JobSkillRequirement(name="Docker", priority="must_have", evidence="Must have Docker containerization"),
        ]
    )

    response = analyzer.analyze(candidate=candidate, job=job)

    py_gap = next(g for g in response.skill_gaps if g.canonical_skill_name == "Python")
    assert py_gap.status == SkillGapStatus.SATISFIED
    assert len(py_gap.candidate_evidence) > 0
    assert any("DataSystems" in ev or "Python" in ev for ev in py_gap.candidate_evidence)
    assert any("Must have Python expertise" in ev for ev in py_gap.job_evidence)

    docker_gap = next(g for g in response.skill_gaps if g.canonical_skill_name == "Docker")
    assert docker_gap.status == SkillGapStatus.MISSING
    assert docker_gap.candidate_evidence == []  # Rule 1: No invented candidate evidence
    assert any("Must have Docker containerization" in ev for ev in docker_gap.job_evidence)


# ---------------------------------------------------------------------------
# Test 9 — Duplicate Normalized Skills Merging
# ---------------------------------------------------------------------------
def test_duplicate_normalized_skills(analyzer):
    """
    JD mentions 'JS' in one clause (nice_to_have, 1 yr) and 'JavaScript' in another (must_have, 3 yr).
    Both resolve to canonical 'JavaScript'.
    Candidate has JavaScript with 2.0 years verified experience.
    RESULT MANDATE:
    - Zero duplicate gap items (len == 1).
    - Canonical skill name is 'JavaScript'.
    - Priority merges to 'must_have' (precedence).
    - Required tenure is 3.0 years (max tenure).
    - Status is INSUFFICIENT with shortfall = 1.0 years.
    """
    candidate = CandidateProfile(
        skills=[SkillItem(name="JavaScript", category="programming_language")],
        experience=[
            ExperienceItem(
                title="Frontend Developer",
                company="WebCo",
                start_date="2022",
                end_date="2024",
                skills=["JavaScript"],
                description="Built React web apps.",
            )
        ],
    )
    job = JobProfile(
        skills=[
            JobSkillRequirement(name="JS", priority="nice_to_have", minimum_years=1.0, evidence="JS familiarity is nice"),
            JobSkillRequirement(name="JavaScript", priority="must_have", minimum_years=3.0, evidence="3+ years JavaScript mandatory"),
        ]
    )

    response = analyzer.analyze(candidate=candidate, job=job)

    assert len(response.skill_gaps) == 1  # Deduplicated!
    gap = response.skill_gaps[0]
    assert gap.canonical_skill_name == "JavaScript"
    assert gap.priority == "must_have"
    assert gap.required_value == "3.0 years"
    assert gap.shortfall == "1.0 years"
    assert gap.status == SkillGapStatus.INSUFFICIENT


# ---------------------------------------------------------------------------
# Test 10 — Summary Arithmetic Invariants
# ---------------------------------------------------------------------------
def test_skill_gap_summary_counts_and_rules(analyzer):
    """
    Verifies all mathematical invariants of SkillGapSummary:
    - total_skill_requirements = satisfied + missing + insufficient + not_evaluable
    - must_have_gaps = missing(must_have) + insufficient(must_have)
    - nice_to_have_gaps = missing(nice_to_have) + insufficient(nice_to_have)
    - not_evaluable is NEVER in must_have_gaps
    """
    candidate = CandidateProfile(
        skills=[
            SkillItem(name="Python", category="programming_language"),
            SkillItem(name="FastAPI", category="framework"),
            SkillItem(name="AWS", category="cloud"),  # lists AWS but no dated experience
        ],
        experience=[
            ExperienceItem(title="Dev", company="C", start_date="2024", end_date="2025", skills=["Python"], description="Python")  # 1 yr
        ],
    )
    job = JobProfile(
        skills=[
            JobSkillRequirement(name="Python", priority="must_have", minimum_years=3.0),  # INSUFFICIENT (must_have)
            JobSkillRequirement(name="FastAPI", priority="must_have"),                    # SATISFIED (must_have)
            JobSkillRequirement(name="PostgreSQL", priority="must_have"),                 # MISSING (must_have)
            JobSkillRequirement(name="AWS", priority="must_have", minimum_years=2.0),     # NOT_EVALUABLE (must_have)
            JobSkillRequirement(name="Docker", priority="nice_to_have"),                  # MISSING (nice_to_have)
        ]
    )

    response = analyzer.analyze(candidate=candidate, job=job)
    s = response.summary

    assert s.total_skill_requirements == 5
    assert s.satisfied_count == 1
    assert s.missing_count == 2       # PostgreSQL, Docker
    assert s.insufficient_count == 1  # Python
    assert s.not_evaluable_count == 1 # AWS

    # Verify arithmetic sum invariant
    assert s.total_skill_requirements == s.satisfied_count + s.missing_count + s.insufficient_count + s.not_evaluable_count

    # Critical Section 11 invariant:
    # must_have_gaps = Python (insufficient) + PostgreSQL (missing) = 2.
    # AWS (not_evaluable) is NOT counted!
    assert s.must_have_gaps == 2
    assert s.nice_to_have_gaps == 1   # Docker (missing)
    assert s.must_have_satisfied == 1 # FastAPI
    assert s.nice_to_have_satisfied == 0


# ---------------------------------------------------------------------------
# Test 11 — No Ranking or Hiring Decisions in Response
# ---------------------------------------------------------------------------
def test_no_ranking_or_hiring_decisions_in_gap_response(analyzer):
    """
    Response schema must contain zero ranking, shortlist, or hiring decision fields.
    """
    candidate = CandidateProfile(skills=[SkillItem(name="Python")])
    job = JobProfile(skills=[JobSkillRequirement(name="Python")])
    response = analyzer.analyze(candidate=candidate, job=job)

    data = response.model_dump()
    forbidden = ["rank", "ranking", "shortlist", "top_n", "leaderboard", "decision", "hire", "reject", "verdict"]
    for key in data.keys():
        assert key.lower() not in forbidden


# ---------------------------------------------------------------------------
# Test 12 — REST API POST /api/v1/gaps/analyze
# ---------------------------------------------------------------------------
def test_api_gaps_analyze_endpoint(client):
    """
    Test dedicated POST /api/v1/gaps/analyze endpoint.
    """
    payload = {
        "candidate": {
            "personal_info": {"name": "Charlie", "email": "charlie@example.com"},
            "skills": [{"name": "Python", "category": "programming_language"}],
        },
        "job": {
            "job_title": "Backend Engineer",
            "skills": [
                {"name": "Python", "priority": "must_have"},
                {"name": "Kubernetes", "priority": "must_have"},
            ],
        },
        "candidate_id": "cand_123",
        "job_id": "job_456",
        "include_semantic": False,
    }

    res = client.post("/api/v1/gaps/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["candidate_id"] == "cand_123"
    assert data["job_id"] == "job_456"
    assert len(data["skill_gaps"]) == 2
    assert data["summary"]["total_skill_requirements"] == 2
    assert data["summary"]["satisfied_count"] == 1
    assert data["summary"]["missing_count"] == 1
    assert data["summary"]["must_have_gaps"] == 1


# ---------------------------------------------------------------------------
# Test 13 — REST API POST /api/v1/gaps/from-files
# ---------------------------------------------------------------------------
def test_api_gaps_from_files_endpoint(client):
    """
    Test POST /api/v1/gaps/from-files with real synthetic PDF documents.
    """
    resume_path = "data/sample/resumes/synthetic_software_engineer.pdf"
    jd_path = "data/sample/job_descriptions/backend_engineer_jd.pdf"

    if not os.path.exists(resume_path) or not os.path.exists(jd_path):
        pytest.skip("Synthetic sample files not found on disk")

    with open(resume_path, "rb") as rf, open(jd_path, "rb") as jf:
        res = client.post(
            "/api/v1/gaps/from-files?include_semantic=false",
            files={
                "resume_file": ("synthetic_software_engineer.pdf", rf.read(), "application/pdf"),
                "job_file": ("backend_engineer_jd.pdf", jf.read(), "application/pdf"),
            },
        )

    assert res.status_code == 200
    data = res.json()
    assert "skill_gaps" in data
    assert "experience_gaps" in data
    assert "summary" in data
    assert data["summary"]["total_skill_requirements"] > 0
    assert len(data["skill_gaps"]) > 0


# ---------------------------------------------------------------------------
# Test 14 — Matching API with include_skill_gaps
# ---------------------------------------------------------------------------
def test_matching_analyze_with_include_skill_gaps(client):
    """
    Test POST /api/v1/matching/analyze with include_skill_gaps=True.
    """
    payload = {
        "candidate": {
            "personal_info": {"name": "Diana", "email": "diana@example.com"},
            "skills": [{"name": "Python", "category": "programming_language"}],
        },
        "job": {
            "job_title": "Developer",
            "skills": [
                {"name": "Python", "priority": "must_have"},
                {"name": "Docker", "priority": "nice_to_have"},
            ],
        },
        "include_semantic": False,
        "include_score": True,
        "include_skill_gaps": True,
    }

    res = client.post("/api/v1/matching/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["gaps"] is not None
    assert "skill_gaps" in data["gaps"]
    assert data["gaps"]["summary"]["total_skill_requirements"] == 2
    assert data["score"] is not None  # Both score and gaps coexist cleanly


# ---------------------------------------------------------------------------
# Test 15 — Matching from Files with include_skill_gaps
# ---------------------------------------------------------------------------
def test_matching_from_files_with_include_skill_gaps(client):
    """
    Test POST /api/v1/matching/from-files?include_skill_gaps=true.
    """
    resume_path = "data/sample/resumes/synthetic_software_engineer.pdf"
    jd_path = "data/sample/job_descriptions/backend_engineer_jd.pdf"

    if not os.path.exists(resume_path) or not os.path.exists(jd_path):
        pytest.skip("Synthetic sample files not found on disk")

    with open(resume_path, "rb") as rf, open(jd_path, "rb") as jf:
        res = client.post(
            "/api/v1/matching/from-files?include_semantic=false&include_score=true&include_skill_gaps=true",
            files={
                "resume_file": ("synthetic_software_engineer.pdf", rf.read(), "application/pdf"),
                "job_file": ("backend_engineer_jd.pdf", jf.read(), "application/pdf"),
            },
        )

    assert res.status_code == 200
    data = res.json()
    assert data["gaps"] is not None
    assert len(data["gaps"]["skill_gaps"]) > 0
    assert data["score"] is not None
