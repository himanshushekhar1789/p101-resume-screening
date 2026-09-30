"""
Comprehensive test suite for Phase 8 Multi-Layer Hybrid Fusion Scoring Engine.

Validates:
1. Perfect candidate scoring and dynamic weight renormalization
2. Missing must-have safety signal (does not auto-zero overall score)
3. Proportional experience fit (candidate_years / required_years)
4. Excess experience capping at 1.0 (no over-rewarding)
5. not_evaluable exclusion from denominator (no unfair failure)
6. Priority weighting (must_have > nice_to_have in rule_fit)
7. Semantic similarity score integration
8. Weight validation (sum != 1.0 rejected)
9. Negative weights rejected
10. LLM unavailable handling and dynamic effective weight renormalization
11. Score bounds [0.0, 1.0]
12. Deterministic reproducibility
13. No ranking fields in output
14. No hiring decision fields in output
15. Configurable weights sanity test (changing weights changes score)
16. Five synthetic candidate benchmark archetypes
17. REST API endpoints (/scoring/analyze, /matching/analyze?include_score=true, /matching/from-files?include_score=true)
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.main import app
from backend.app.schemas import (
    CandidateProfile,
    PersonalInfo,
    SkillItem,
    NormalizedSkill,
    ExperienceItem,
    EducationItem,
    JobProfile,
    JobSkillRequirement,
    JobExperienceRequirement,
    JobEducationRequirement,
    SingleRequirementMatch,
    RequirementReference,
    MatchStatus,
    MatchMethod,
    SemanticStatus,
    SemanticMatchResult,
    CandidateJobMatchResponse,
    MatchingSummary,
    ScoringWeights,
    CandidateJobScoreResponse,
    ScoringAnalyzeRequest,
)
from backend.app.services.scoring_engine import (
    ScoringEngine,
    get_scoring_engine,
    extract_duration_years,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def scoring_engine():
    return ScoringEngine()


# ---------------------------------------------------------------------------
# Test Helper Builders
# ---------------------------------------------------------------------------
def make_mock_match(
    name: str,
    req_type: str = "skill",
    priority: str = "must_have",
    status: MatchStatus = MatchStatus.MATCHED,
    method: MatchMethod = MatchMethod.CANONICAL_EXACT,
    minimum_years: float = None,
    candidate_years: float = None,
    reason: str = None,
    semantic_sim: float = None,
) -> SingleRequirementMatch:
    """Helper to synthesize a SingleRequirementMatch with exact properties."""
    req_ref = RequirementReference(
        name=name,
        type=req_type,
        priority=priority,
        minimum_years=minimum_years,
        context=f"{minimum_years}+ years {name}" if minimum_years else name,
    )
    cand_ev = []
    if candidate_years is not None:
        cand_ev.append(f"Candidate tenure: ~{candidate_years} years")

    if reason is None:
        if candidate_years is not None and minimum_years is not None:
            reason = f"Candidate has ~{candidate_years} years of {name} (>= {minimum_years} required)."
        else:
            reason = f"Match evaluated: {status.value}"

    sem_res = None
    if semantic_sim is not None:
        sem_res = SemanticMatchResult(
            requirement_id=f"{req_type}_{name}",
            requirement_text=name,
            category=req_type,
            priority=priority,
            similarity=semantic_sim,
            semantic_status=SemanticStatus.SEMANTIC_MATCH if semantic_sim >= 0.75 else SemanticStatus.SEMANTIC_PARTIAL,
            candidate_evidence="Mock evidence",
            candidate_source="skills",
            candidate_text="Mock text",
            explanation=f"Similarity {semantic_sim}",
        )

    return SingleRequirementMatch(
        requirement=req_ref,
        status=status,
        match_method=method,
        candidate_evidence=cand_ev,
        requirement_evidence=[name],
        reason=reason,
        semantic_result=sem_res,
    )


# ---------------------------------------------------------------------------
# Test 1 — Perfect Candidate
# ---------------------------------------------------------------------------
def test_perfect_candidate_scoring(scoring_engine):
    """
    Candidate satisfies all must-haves and nice-to-haves with verified experience.
    Rule fit = 1.0, experience fit = 1.0, semantic fit is high.
    Effective weights are renormalized when LLM is unavailable.
    """
    matches = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.95),
        make_mock_match("FastAPI", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.92),
        make_mock_match("Docker", "skill", "nice_to_have", MatchStatus.MATCHED, semantic_sim=0.88),
        make_mock_match("Experience", "experience", "must_have", MatchStatus.MATCHED, MatchMethod.EXPERIENCE_VERIFIED, minimum_years=5.0, candidate_years=5.0),
    ]
    resp = CandidateJobMatchResponse(
        matches=matches,
        summary=MatchingSummary(total_requirements=4, matched=4, must_have_total=3, must_have_matched=3, nice_to_have_total=1, nice_to_have_matched=1),
    )

    score_result = scoring_engine.compute_score(resp)

    assert score_result.rule_fit_score == 1.0
    assert score_result.experience_fit_score == 1.0
    assert score_result.semantic_fit_score is not None and score_result.semantic_fit_score > 0.90
    assert score_result.all_must_haves_satisfied is True

    # Check dynamic weight renormalization (0.30 + 0.40 + 0.20 = 0.90)
    assert score_result.weights_renormalized is True
    assert score_result.components.llm_fit.available is False
    assert round(score_result.components.rule_fit.effective_weight, 4) == round(0.30 / 0.90, 4)
    assert round(score_result.components.semantic_fit.effective_weight, 4) == round(0.40 / 0.90, 4)
    assert round(score_result.components.experience_fit.effective_weight, 4) == round(0.20 / 0.90, 4)
    assert score_result.candidate_fit_score > 0.95


# ---------------------------------------------------------------------------
# Test 2 — Missing Must-Have
# ---------------------------------------------------------------------------
def test_missing_must_have_safety_signal(scoring_engine):
    """
    Candidate misses a critical must-have.
    all_must_haves_satisfied must be False, rule_fit decreases, but overall_fit is NOT forced to 0.
    """
    matches = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.95),
        make_mock_match("PostgreSQL", "skill", "must_have", MatchStatus.UNMATCHED, MatchMethod.UNMATCHED, semantic_sim=0.10),
        make_mock_match("Docker", "skill", "nice_to_have", MatchStatus.MATCHED, semantic_sim=0.85),
        make_mock_match("Experience", "experience", "must_have", MatchStatus.MATCHED, minimum_years=3.0, candidate_years=4.0),
    ]
    resp = CandidateJobMatchResponse(
        matches=matches,
        summary=MatchingSummary(total_requirements=4, matched=3, unmatched=1, must_have_total=3, must_have_matched=2),
    )

    score_result = scoring_engine.compute_score(resp)

    assert score_result.all_must_haves_satisfied is False
    assert score_result.rule_fit_score < 1.0
    # Rule fit calculation: (1.0*1.0 + 0.0*1.0 + 1.0*0.5 + 1.0*1.0) / (1.0 + 1.0 + 0.5 + 1.0) = 2.5 / 3.5 = 0.7143
    assert abs(score_result.rule_fit_score - 0.7143) < 0.001
    # Crucially, candidate_fit_score > 0.0 (not artificially zeroed out)
    assert score_result.candidate_fit_score > 0.50


# ---------------------------------------------------------------------------
# Test 3 — Partial Experience (Proportional Calculation)
# ---------------------------------------------------------------------------
def test_partial_experience_proportional(scoring_engine):
    """
    Required: 5.0 years, Candidate: 2.0 years.
    Proportional experience fit = 2.0 / 5.0 = 0.40.
    """
    matches = [
        make_mock_match("Software Engineering", "experience", "must_have", MatchStatus.PARTIAL, MatchMethod.EXPERIENCE_INSUFFICIENT, minimum_years=5.0, candidate_years=2.0),
    ]
    resp = CandidateJobMatchResponse(
        matches=matches,
        summary=MatchingSummary(total_requirements=1, partial=1, must_have_total=1),
    )

    score_result = scoring_engine.compute_score(resp)
    assert score_result.experience_fit_score == 0.40


# ---------------------------------------------------------------------------
# Test 4 — Excess Experience Capped at 1.0
# ---------------------------------------------------------------------------
def test_excess_experience_capped(scoring_engine):
    """
    Required: 5.0 years, Candidate: 8.0 years.
    Experience fit must cap at 1.0 and NOT award bonus points above 1.0.
    """
    matches = [
        make_mock_match("Software Engineering", "experience", "must_have", MatchStatus.MATCHED, MatchMethod.EXPERIENCE_VERIFIED, minimum_years=5.0, candidate_years=8.0),
    ]
    resp = CandidateJobMatchResponse(
        matches=matches,
        summary=MatchingSummary(total_requirements=1, matched=1, must_have_total=1),
    )

    score_result = scoring_engine.compute_score(resp)
    assert score_result.experience_fit_score == 1.0


# ---------------------------------------------------------------------------
# Test 5 — Not Evaluable Handling (Excluded from Denominator)
# ---------------------------------------------------------------------------
def test_not_evaluable_excluded_from_denominator(scoring_engine):
    """
    Candidate has Python listed, but no explicit dates (Phase 6 returns not_evaluable).
    JD also has general experience of 4.0 years (candidate has 4.0 years).
    The not_evaluable requirement must be excluded from the experience denominator.
    """
    matches = [
        make_mock_match("Python Tenure", "skill", "must_have", MatchStatus.NOT_EVALUABLE, MatchMethod.NOT_EVALUABLE, minimum_years=3.0),
        make_mock_match("General Experience", "experience", "must_have", MatchStatus.MATCHED, MatchMethod.EXPERIENCE_VERIFIED, minimum_years=4.0, candidate_years=4.0),
    ]
    resp = CandidateJobMatchResponse(
        matches=matches,
        summary=MatchingSummary(total_requirements=2, matched=1, not_evaluable=1),
    )

    score_result = scoring_engine.compute_score(resp)
    # The not_evaluable skill tenure was excluded; the general experience requirement yields 1.0
    assert score_result.experience_fit_score == 1.0
    assert score_result.not_evaluable_requirements >= 1


# ---------------------------------------------------------------------------
# Test 6 — Priority Weighting (Must-Have > Nice-To-Have)
# ---------------------------------------------------------------------------
def test_priority_weighting_rule_fit(scoring_engine):
    """
    Must-have requirements (weight 1.0) must carry greater weight in rule_fit than nice-to-have (0.5).
    """
    # Candidate A matches must-have, misses nice-to-have
    matches_a = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED),
        make_mock_match("Docker", "skill", "nice_to_have", MatchStatus.UNMATCHED),
    ]
    resp_a = CandidateJobMatchResponse(matches=matches_a, summary=MatchingSummary(total_requirements=2))
    score_a = scoring_engine.compute_score(resp_a)

    # Candidate B misses must-have, matches nice-to-have
    matches_b = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.UNMATCHED),
        make_mock_match("Docker", "skill", "nice_to_have", MatchStatus.MATCHED),
    ]
    resp_b = CandidateJobMatchResponse(matches=matches_b, summary=MatchingSummary(total_requirements=2))
    score_b = scoring_engine.compute_score(resp_b)

    # Score A: (1.0 * 1.0 + 0.0 * 0.5) / 1.5 = 1.0 / 1.5 = 0.6667
    # Score B: (0.0 * 1.0 + 1.0 * 0.5) / 1.5 = 0.5 / 1.5 = 0.3333
    assert score_a.rule_fit_score > score_b.rule_fit_score
    assert abs(score_a.rule_fit_score - 0.6667) < 0.001
    assert abs(score_b.rule_fit_score - 0.3333) < 0.001


# ---------------------------------------------------------------------------
# Test 7 — Semantic Score Integration
# ---------------------------------------------------------------------------
def test_semantic_score_integration(scoring_engine):
    """
    Verify raw Phase 7 semantic similarity values are correctly aggregated by priority.
    """
    matches = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.90),
        make_mock_match("FastAPI", "skill", "nice_to_have", MatchStatus.MATCHED, semantic_sim=0.70),
    ]
    resp = CandidateJobMatchResponse(matches=matches, summary=MatchingSummary(total_requirements=2))
    score_res = scoring_engine.compute_score(resp)

    # Expected: (0.90 * 1.0 + 0.70 * 0.5) / (1.0 + 0.5) = (0.90 + 0.35) / 1.5 = 1.25 / 1.5 = 0.8333
    assert abs(score_res.semantic_fit_score - 0.8333) < 0.001


# ---------------------------------------------------------------------------
# Test 8 — Weight Validation (Sum != 1.0 Rejected)
# ---------------------------------------------------------------------------
def test_weight_validation_sum_rejection():
    """
    Supplying weights that do not sum to 1.0 must raise a ValidationError / ValueError.
    """
    with pytest.raises(ValidationError):
        ScoringWeights(
            rule_weight=0.30,
            semantic_weight=0.40,
            experience_weight=0.20,
            llm_weight=0.20,  # Sum = 1.10
        )

    with pytest.raises(ValidationError):
        ScoringWeights(
            rule_weight=0.20,
            semantic_weight=0.20,
            experience_weight=0.20,
            llm_weight=0.20,  # Sum = 0.80
        )


# ---------------------------------------------------------------------------
# Test 9 — Negative Weights Rejected
# ---------------------------------------------------------------------------
def test_negative_weights_rejected():
    """
    Supplying a negative weight must fail validation.
    """
    with pytest.raises(ValidationError):
        ScoringWeights(
            rule_weight=0.60,
            semantic_weight=-0.20,
            experience_weight=0.40,
            llm_weight=0.20,
        )


# ---------------------------------------------------------------------------
# Test 10 — LLM Unavailable & Dynamic Renormalization
# ---------------------------------------------------------------------------
def test_llm_unavailable_dynamic_renormalization(scoring_engine):
    """
    When LLM fit is unavailable, effective weights renormalize:
    Rule: 0.30 / 0.90 = 0.3333
    Semantic: 0.40 / 0.90 = 0.4444
    Experience: 0.20 / 0.90 = 0.2222
    """
    matches = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=1.0),
        make_mock_match("Experience", "experience", "must_have", MatchStatus.MATCHED, minimum_years=5.0, candidate_years=5.0),
    ]
    resp = CandidateJobMatchResponse(matches=matches, summary=MatchingSummary(total_requirements=2))

    score_res = scoring_engine.compute_score(resp, llm_fit_score=None)

    assert score_res.components.llm_fit.available is False
    assert score_res.components.llm_fit.effective_weight == 0.0
    assert score_res.weights_renormalized is True
    assert round(score_res.components.rule_fit.effective_weight, 3) == 0.333
    assert round(score_res.components.semantic_fit.effective_weight, 3) == 0.444
    assert round(score_res.components.experience_fit.effective_weight, 3) == 0.222


# ---------------------------------------------------------------------------
# Test 11 — Score Bounds [0.0, 1.0]
# ---------------------------------------------------------------------------
def test_score_bounds_and_clamping(scoring_engine):
    """
    Every score must be strictly within [0.0, 1.0], and percentage in [0.0, 100.0].
    """
    # Worst case: all unmatched
    matches_worst = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.UNMATCHED, semantic_sim=0.0),
        make_mock_match("Experience", "experience", "must_have", MatchStatus.UNMATCHED, minimum_years=5.0, candidate_years=0.0),
    ]
    score_worst = scoring_engine.compute_score(
        CandidateJobMatchResponse(matches=matches_worst, summary=MatchingSummary(total_requirements=2))
    )
    assert 0.0 <= score_worst.candidate_fit_score <= 1.0
    assert score_worst.candidate_fit_score == 0.0
    assert score_worst.percentage_score == 0.0

    # Best case: all matched
    matches_best = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=1.0),
        make_mock_match("Experience", "experience", "must_have", MatchStatus.MATCHED, minimum_years=5.0, candidate_years=10.0),
    ]
    score_best = scoring_engine.compute_score(
        CandidateJobMatchResponse(matches=matches_best, summary=MatchingSummary(total_requirements=2))
    )
    assert 0.0 <= score_best.candidate_fit_score <= 1.0
    assert score_best.candidate_fit_score == 1.0
    assert score_best.percentage_score == 100.0


# ---------------------------------------------------------------------------
# Test 12 — Score Reproducibility
# ---------------------------------------------------------------------------
def test_score_reproducibility(scoring_engine):
    """
    Identical inputs must yield bitwise identical scores.
    """
    matches = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.85),
        make_mock_match("Docker", "skill", "nice_to_have", MatchStatus.PARTIAL, semantic_sim=0.65),
        make_mock_match("Tenure", "experience", "must_have", MatchStatus.MATCHED, minimum_years=4.0, candidate_years=3.0),
    ]
    resp = CandidateJobMatchResponse(matches=matches, summary=MatchingSummary(total_requirements=3))

    score_1 = scoring_engine.compute_score(resp)
    score_2 = scoring_engine.compute_score(resp)

    assert score_1.candidate_fit_score == score_2.candidate_fit_score
    assert score_1.rule_fit_score == score_2.rule_fit_score
    assert score_1.semantic_fit_score == score_2.semantic_fit_score
    assert score_1.experience_fit_score == score_2.experience_fit_score


# ---------------------------------------------------------------------------
# Test 13 — No Ranking in Response Schema
# ---------------------------------------------------------------------------
def test_no_ranking_or_shortlist_in_response(scoring_engine):
    """
    Verify the response model contains zero ranking fields (rank, shortlist, top_n, etc.).
    """
    matches = [make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED)]
    resp = CandidateJobMatchResponse(matches=matches, summary=MatchingSummary(total_requirements=1))
    score_res = scoring_engine.compute_score(resp)

    dumped = score_res.model_dump()
    forbidden_terms = ["rank", "ranking", "shortlist", "top_n", "leaderboard", "position"]
    for key in dumped.keys():
        assert key.lower() not in forbidden_terms


# ---------------------------------------------------------------------------
# Test 14 — No Hiring Decision in Response Schema
# ---------------------------------------------------------------------------
def test_no_hiring_decision_in_response(scoring_engine):
    """
    Verify the response contains zero decision fields (hire, reject, selected, etc.).
    """
    matches = [make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED)]
    resp = CandidateJobMatchResponse(matches=matches, summary=MatchingSummary(total_requirements=1))
    score_res = scoring_engine.compute_score(resp)

    dumped = score_res.model_dump()
    forbidden_decision_terms = ["decision", "hire", "reject", "selected", "verdict", "recommendation"]
    for key in dumped.keys():
        assert key.lower() not in forbidden_decision_terms


# ---------------------------------------------------------------------------
# Test 15 — Configurable Weights Sanity Test
# ---------------------------------------------------------------------------
def test_configurable_weights_sanity(scoring_engine):
    """
    Demonstrates that the engine is configurable: changing weights changes the overall score predictably.
    """
    # Candidate has high rule fit (1.0), but lower semantic fit (0.50), and perfect experience (1.0)
    matches = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.50),
        make_mock_match("Experience", "experience", "must_have", MatchStatus.MATCHED, minimum_years=3.0, candidate_years=3.0),
    ]
    resp = CandidateJobMatchResponse(matches=matches, summary=MatchingSummary(total_requirements=2))

    # Config A: heavy on semantic (0.50)
    weights_a = ScoringWeights(rule_weight=0.20, semantic_weight=0.60, experience_weight=0.20, llm_weight=0.0)
    score_a = scoring_engine.compute_score(resp, weights=weights_a)

    # Config B: heavy on rule (0.60)
    weights_b = ScoringWeights(rule_weight=0.60, semantic_weight=0.20, experience_weight=0.20, llm_weight=0.0)
    score_b = scoring_engine.compute_score(resp, weights=weights_b)

    # Config B should produce higher fit than Config A because candidate is strong in rule fit
    assert score_b.candidate_fit_score > score_a.candidate_fit_score
    assert score_a.candidate_fit_score != score_b.candidate_fit_score


# ---------------------------------------------------------------------------
# Test 16 — Five Synthetic Score Benchmarks (Section 36)
# ---------------------------------------------------------------------------
def test_five_synthetic_score_benchmarks(scoring_engine):
    """
    Evaluates the 5 mandated archetypes from Section 36:
    Candidate A — Strong Match
    Candidate B — Missing Critical Requirement
    Candidate C — Strong Skills, Low Experience
    Candidate D — Strong Experience, Weak Skill Fit
    Candidate E — Sparse Resume (Many Not Evaluable)
    """
    # Candidate A — Strong Match
    matches_a = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.95),
        make_mock_match("FastAPI", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.92),
        make_mock_match("Docker", "skill", "nice_to_have", MatchStatus.MATCHED, semantic_sim=0.88),
        make_mock_match("Experience", "experience", "must_have", MatchStatus.MATCHED, minimum_years=5.0, candidate_years=6.0),
    ]
    res_a = scoring_engine.compute_score(CandidateJobMatchResponse(matches=matches_a, summary=MatchingSummary(total_requirements=4, matched=4)))
    assert res_a.candidate_fit_score >= 0.90
    assert res_a.all_must_haves_satisfied is True

    # Candidate B — Missing Critical Requirement
    matches_b = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.95),
        make_mock_match("PostgreSQL", "skill", "must_have", MatchStatus.UNMATCHED, semantic_sim=0.10),
        make_mock_match("Docker", "skill", "nice_to_have", MatchStatus.MATCHED, semantic_sim=0.85),
        make_mock_match("Experience", "experience", "must_have", MatchStatus.MATCHED, minimum_years=5.0, candidate_years=5.0),
    ]
    res_b = scoring_engine.compute_score(CandidateJobMatchResponse(matches=matches_b, summary=MatchingSummary(total_requirements=4)))
    assert res_b.all_must_haves_satisfied is False
    assert res_b.rule_fit_score < res_a.rule_fit_score

    # Candidate C — Strong Skills, Low Experience
    matches_c = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.95),
        make_mock_match("FastAPI", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.92),
        make_mock_match("Experience", "experience", "must_have", MatchStatus.PARTIAL, minimum_years=5.0, candidate_years=1.5),
    ]
    res_c = scoring_engine.compute_score(CandidateJobMatchResponse(matches=matches_c, summary=MatchingSummary(total_requirements=3)))
    assert res_c.experience_fit_score == 0.30
    assert res_c.rule_fit_score > res_c.experience_fit_score

    # Candidate D — Strong Experience, Weak Skill Fit
    matches_d = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.UNMATCHED, semantic_sim=0.20),
        make_mock_match("FastAPI", "skill", "must_have", MatchStatus.UNMATCHED, semantic_sim=0.15),
        make_mock_match("Experience", "experience", "must_have", MatchStatus.MATCHED, minimum_years=5.0, candidate_years=10.0),
    ]
    res_d = scoring_engine.compute_score(CandidateJobMatchResponse(matches=matches_d, summary=MatchingSummary(total_requirements=3)))
    assert res_d.experience_fit_score == 1.0
    assert res_d.rule_fit_score < res_d.experience_fit_score
    assert res_d.rule_fit_score <= 0.35

    # Candidate E — Sparse Resume (Many Not Evaluable)
    matches_e = [
        make_mock_match("Python", "skill", "must_have", MatchStatus.MATCHED, semantic_sim=0.80),
        make_mock_match("PostgreSQL Tenure", "skill", "must_have", MatchStatus.NOT_EVALUABLE),
        make_mock_match("AWS Tenure", "skill", "nice_to_have", MatchStatus.NOT_EVALUABLE),
    ]
    res_e = scoring_engine.compute_score(CandidateJobMatchResponse(matches=matches_e, summary=MatchingSummary(total_requirements=3)))
    assert res_e.not_evaluable_requirements == 2
    # Not evaluable excluded, candidate evaluated on the single evaluable requirement
    assert res_e.rule_fit_score == 1.0


# ---------------------------------------------------------------------------
# Test 17 — REST API Endpoints
# ---------------------------------------------------------------------------
def test_api_scoring_analyze_endpoint(client):
    """
    Test POST /api/v1/scoring/analyze with structured CandidateProfile and JobProfile.
    """
    candidate_payload = {
        "personal_info": {"name": "Alice Smith", "email": "alice@example.com"},
        "skills": [{"name": "Python", "category": "programming_language"}, {"name": "FastAPI", "category": "framework"}],
        "normalized_skills": [
            {"canonical_name": "Python", "original_name": "Python", "category": "programming_language"},
            {"canonical_name": "FastAPI", "original_name": "FastAPI", "category": "framework"},
        ],
        "experience": [
            {"title": "Backend Dev", "company": "TechCorp", "start_date": "2021", "end_date": "2024", "skills": ["Python", "FastAPI"]}
        ],
    }

    job_payload = {
        "job_title": "Backend Engineer",
        "skills": [
            {"name": "Python", "priority": "must_have"},
            {"name": "FastAPI", "priority": "must_have"},
        ],
        "experience_requirements": [
            {"text": "3+ years experience", "minimum_years": 3.0, "priority": "must_have"}
        ],
    }

    response = client.post(
        "/api/v1/scoring/analyze",
        json={
            "candidate": candidate_payload,
            "job": job_payload,
            "candidate_id": "cand_001",
            "job_id": "job_001",
            "include_semantic": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "candidate_fit_score" in data
    assert "components" in data
    assert "rule_fit" in data["components"]
    assert "semantic_fit" in data["components"]
    assert "experience_fit" in data["components"]
    assert "llm_fit" in data["components"]
    assert data["candidate_id"] == "cand_001"
    assert data["job_id"] == "job_001"
    assert 0.0 <= data["candidate_fit_score"] <= 1.0


def test_api_matching_analyze_with_include_score(client):
    """
    Test POST /api/v1/matching/analyze with include_score=True.
    """
    candidate_payload = {
        "personal_info": {"name": "Bob", "email": "bob@example.com"},
        "skills": [{"name": "Python", "category": "programming_language"}],
        "normalized_skills": [{"canonical_name": "Python", "original_name": "Python", "category": "programming_language"}],
    }
    job_payload = {
        "job_title": "Junior Python Dev",
        "skills": [{"name": "Python", "priority": "must_have"}],
    }

    response = client.post(
        "/api/v1/matching/analyze",
        json={
            "candidate": candidate_payload,
            "job": job_payload,
            "include_semantic": False,
            "include_score": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["score"] is not None
    assert "candidate_fit_score" in data["score"]
    assert data["score"]["rule_fit_score"] == 1.0


def test_api_matching_from_files_with_include_score(client):
    """
    Test POST /api/v1/matching/from-files with include_score=True.
    """
    import os
    resume_path = "data/sample/resumes/synthetic_software_engineer.pdf"
    jd_path = "data/sample/job_descriptions/backend_engineer_jd.pdf"

    if not os.path.exists(resume_path) or not os.path.exists(jd_path):
        pytest.skip("Synthetic sample files not found")

    with open(resume_path, "rb") as rf, open(jd_path, "rb") as jf:
        response = client.post(
            "/api/v1/matching/from-files?include_semantic=false&include_score=true",
            files={
                "resume_file": ("synthetic_software_engineer.pdf", rf.read(), "application/pdf"),
                "job_file": ("backend_engineer_jd.pdf", jf.read(), "application/pdf"),
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert "score" in data
    assert data["score"] is not None
    assert "candidate_fit_score" in data["score"]
    assert 0.0 <= data["score"]["candidate_fit_score"] <= 1.0


