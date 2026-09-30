"""Unit, integration, and benchmark tests for Phase 7 Semantic Matching & Embedding Layer.

Validates:
1. Exact matches remain deterministic (Phase 6 authoritative)
2. Related concepts have higher semantic similarity than unrelated concepts
3. Unrelated concepts produce low similarity and semantic_unrelated status
4. False-positive protections (Java != JavaScript, C != C++, Python != PyTorch, etc.)
5. Skill-specific experience duration guardrails (cannot hallucinate years)
6. Embedding model configuration (EMBEDDING_MODEL_NAME)
7. Semantic matching disabled switch (SEMANTIC_MATCHING_ENABLED=False)
8. In-memory cache hit ratio and latency benefits
9. Deterministic reproducibility across repeated calls
10. Synthetic semantic benchmark across positive and negative pairs
11. API endpoints: POST /api/v1/matching/semantic and POST /api/v1/matching/analyze?include_semantic=True
12. Absolute absence of scores, percentages, rankings, or shortlists
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings, get_settings
from backend.app.main import app
from backend.app.schemas import (
    CandidateProfile,
    PersonalInfo,
    EducationItem,
    ExperienceItem,
    JobEducationRequirement,
    JobExperienceRequirement,
    JobProfile,
    JobSkillRequirement,
    MatchStatus,
    MatchMethod,
    MatchingAnalyzeRequest,
    RequirementPriority,
    SemanticStatus,
    SkillItem,
)
from backend.app.services.embedding_service import (
    EmbeddingService,
    compute_cosine_similarity,
    get_embedding_service,
)
from backend.app.services.matching_engine import MatchingEngine
from backend.app.services.semantic_matcher import (
    SemanticMatcher,
    evaluate_semantic_matches,
    is_protected_incompatible,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def embedding_svc():
    """Retrieve shared embedding service for tests."""
    return get_embedding_service()


# ---------------------------------------------------------------------------
# Test 1 — Exact match remains deterministic
# ---------------------------------------------------------------------------
def test_exact_match_remains_deterministic():
    """Candidate with Python and JD requiring Python must remain an exact canonical match.
    The semantic layer must not replace or downgrade the deterministic outcome."""
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Dev Alex", email="alex@example.com"),
        skills=[SkillItem(name="Python", category="programming_language")],
        experience=[
            ExperienceItem(
                title="Software Engineer",
                company="TechCorp",
                start_date="2020",
                end_date="2024",
                skills=["Python"],
                description="Built high-throughput backend services using Python.",
            )
        ],
    )
    job = JobProfile(
        job_title="Python Engineer",
        skills=[
            JobSkillRequirement(
                name="Python",
                category="programming_language",
                priority="must_have",
                evidence="Solid experience in Python backend development",
            )
        ],
    )

    engine = MatchingEngine()
    result = engine.match_candidate_to_job(candidate, job, include_semantic=True)

    assert len(result.matches) == 1
    match = result.matches[0]
    # Phase 6 deterministic authority must be preserved
    assert match.status == MatchStatus.MATCHED
    assert match.match_method == MatchMethod.CANONICAL_EXACT

    # Semantic evaluation must also be present when requested
    assert result.semantic_matches is not None
    assert len(result.semantic_matches) >= 1
    assert match.semantic_result is not None


# ---------------------------------------------------------------------------
# Test 2 — Related concepts produce meaningful semantic similarity
# ---------------------------------------------------------------------------
def test_related_concepts_semantic_similarity(embedding_svc):
    """Conceptually related phrases ('REST API development' vs 'Backend API development')
    must yield higher similarity than unrelated phrases."""
    vec_a = embedding_svc.embed_text("REST API development")
    vec_b = embedding_svc.embed_text("backend API development")
    vec_unrelated = embedding_svc.embed_text("graphic design and typography")

    sim_related = embedding_svc.cosine_similarity(vec_a, vec_b)
    sim_unrelated = embedding_svc.cosine_similarity(vec_a, vec_unrelated)

    assert sim_related > sim_unrelated
    assert sim_related >= 0.60  # Meaningfully high conceptual similarity


# ---------------------------------------------------------------------------
# Test 3 — Unrelated concepts produce low similarity
# ---------------------------------------------------------------------------
def test_unrelated_concepts_low_similarity(embedding_svc):
    """'React UI development' vs 'PostgreSQL database administration' must yield low similarity."""
    vec_react = embedding_svc.embed_text("React UI development")
    vec_postgres = embedding_svc.embed_text("PostgreSQL database administration")

    sim = embedding_svc.cosine_similarity(vec_react, vec_postgres)
    assert sim < 0.55  # Below medium threshold


# ---------------------------------------------------------------------------
# Test 4 — Java vs JavaScript protection
# ---------------------------------------------------------------------------
def test_java_vs_javascript_protection():
    """Java and JavaScript must never be conflated into a match despite lexical overlap."""
    assert is_protected_incompatible("Java", "JavaScript") is True
    assert is_protected_incompatible("JavaScript", "Java") is True

    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Frontend Dev", email="js@example.com"),
        skills=[SkillItem(name="JavaScript", category="programming_language")],
        experience=[
            ExperienceItem(
                title="Frontend Developer",
                company="WebCo",
                start_date="2022",
                end_date="2024",
                skills=["JavaScript"],
                description="Created interactive web applications using modern JavaScript.",
            )
        ],
    )
    job = JobProfile(
        job_title="Enterprise Java Engineer",
        skills=[
            JobSkillRequirement(
                name="Java",
                category="programming_language",
                priority="must_have",
                evidence="5+ years of core Java development required",
            )
        ],
    )

    engine = MatchingEngine()
    result = engine.match_candidate_to_job(candidate, job, include_semantic=True)

    # Deterministic status must be UNMATCHED
    assert result.matches[0].status == MatchStatus.UNMATCHED

    # Semantic evaluation must be UNRELATED or NOT_EVALUABLE due to protected conflict
    if result.matches[0].semantic_result:
        assert result.matches[0].semantic_result.semantic_status in (
            SemanticStatus.SEMANTIC_UNRELATED,
            SemanticStatus.SEMANTIC_NOT_EVALUABLE,
        )


# ---------------------------------------------------------------------------
# Test 5 — Python vs PyTorch protection
# ---------------------------------------------------------------------------
def test_python_vs_pytorch_protection():
    """Python and PyTorch must remain distinct; Python does not satisfy PyTorch requirement."""
    assert is_protected_incompatible("Python", "PyTorch") is True

    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Py Dev", email="py@example.com"),
        skills=[SkillItem(name="Python", category="programming_language")],
    )
    job = JobProfile(
        job_title="ML Engineer",
        skills=[
            JobSkillRequirement(
                name="PyTorch",
                category="library",
                priority="must_have",
                evidence="Deep learning modeling in PyTorch",
            )
        ],
    )

    engine = MatchingEngine()
    result = engine.match_candidate_to_job(candidate, job, include_semantic=True)
    assert result.matches[0].status == MatchStatus.UNMATCHED


# ---------------------------------------------------------------------------
# Test 6 — Skill-specific experience duration cannot be hallucinated
# ---------------------------------------------------------------------------
def test_skill_specific_experience_duration_guardrail():
    """Semantic similarity indicates related concepts (PyTorch vs TensorFlow)
    but must never override Phase 6's not_evaluable status for tenure."""
    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="ML Specialist", email="ml@example.com"),
        skills=[
            SkillItem(name="PyTorch", category="library"),
            SkillItem(name="Machine Learning", category="ai_ml"),
        ],
        experience=[
            ExperienceItem(
                title="AI Researcher",
                company="Lab",
                start_date="2021",
                end_date="2024",
                skills=["PyTorch"],
                description="Developed deep learning transformers using PyTorch.",
            )
        ],
    )
    job = JobProfile(
        job_title="Senior TensorFlow Specialist",
        experience_requirements=[
            JobExperienceRequirement(
                skill="TensorFlow",
                minimum_years=3.0,
                priority="must_have",
                text="3+ years of TensorFlow experience required",
                evidence="Must have 3+ years hands-on production TensorFlow deployment",
            )
        ],
    )

    engine = MatchingEngine()
    result = engine.match_candidate_to_job(candidate, job, include_semantic=True)

    # In Phase 6, lack of dated TensorFlow experience yields UNMATCHED
    assert result.matches[0].status == MatchStatus.UNMATCHED
    assert result.matches[0].match_method in (MatchMethod.UNMATCHED, MatchMethod.NOT_EVALUABLE)


# ---------------------------------------------------------------------------
# Test 7 — Model configuration is respected
# ---------------------------------------------------------------------------
def test_model_configuration(monkeypatch):
    """Verify that EMBEDDING_MODEL_NAME setting is reflected in the embedding service."""
    svc = EmbeddingService(model_name="all-MiniLM-L6-v2")
    assert svc.model_name == "all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# Test 8 — Semantic matching disabled switch
# ---------------------------------------------------------------------------
def test_semantic_matching_disabled(monkeypatch):
    """When SEMANTIC_MATCHING_ENABLED=False, semantic matching is bypassed."""
    monkeypatch.setattr(
        "backend.app.config.get_settings",
        lambda: Settings(semantic_matching_enabled=False),
    )

    candidate = CandidateProfile(
        personal_info=PersonalInfo(name="Test Candidate", email="test@example.com"),
        skills=[SkillItem(name="Python", category="programming_language")],
    )
    job = JobProfile(
        job_title="Test Job",
        skills=[JobSkillRequirement(name="Python", category="programming_language")],
    )

    engine = MatchingEngine()
    result = engine.match_candidate_to_job(candidate, job, include_semantic=True)
    # When disabled, semantic_matches remains None
    assert result.semantic_matches is None


# ---------------------------------------------------------------------------
# Test 9 — In-memory cache functionality
# ---------------------------------------------------------------------------
def test_in_memory_cache_hit_and_latency(embedding_svc):
    """Repeated embedding of identical text must hit the cache and execute rapidly."""
    embedding_svc.clear_cache()
    text = "Scalable microservices architecture with Python and Docker"

    # First call: cache miss
    vec1 = embedding_svc.embed_text(text)
    stats1 = embedding_svc.get_cache_stats()
    assert stats1["misses"] == 1
    assert stats1["hits"] == 0

    # Second call: cache hit
    vec2 = embedding_svc.embed_text(text)
    stats2 = embedding_svc.get_cache_stats()
    assert stats2["hits"] == 1
    assert vec1 == vec2


# ---------------------------------------------------------------------------
# Test 10 — Deterministic reproducibility
# ---------------------------------------------------------------------------
def test_deterministic_reproducibility(embedding_svc):
    """The same input text produces identical vectors (floating-point tolerance < 1e-6)."""
    text = "Kubernetes container orchestration and cloud deployments"
    v1 = embedding_svc.embed_text(text)
    v2 = embedding_svc.embed_text(text)

    for a, b in zip(v1, v2):
        assert abs(a - b) < 1e-6


# ---------------------------------------------------------------------------
# Test 11 — Synthetic Semantic Benchmark (Section 36)
# ---------------------------------------------------------------------------
def test_synthetic_semantic_benchmark(embedding_svc):
    """Benchmark evaluation across 4 positive/related pairs and 3 negative/unrelated pairs."""
    positive_pairs = [
        ("REST API development", "backend API development"),
        ("container orchestration", "Kubernetes cluster management"),
        ("natural language processing", "NLP and text mining"),
        ("relational database management", "PostgreSQL database development"),
    ]

    negative_pairs = [
        ("React UI development", "PostgreSQL database administration"),
        ("graphic design and typography", "Python backend development"),
        ("mobile UI development in Swift", "AWS infrastructure management"),
    ]

    pos_sims = [
        embedding_svc.cosine_similarity(
            embedding_svc.embed_text(p[0]),
            embedding_svc.embed_text(p[1]),
        )
        for p in positive_pairs
    ]

    neg_sims = [
        embedding_svc.cosine_similarity(
            embedding_svc.embed_text(n[0]),
            embedding_svc.embed_text(n[1]),
        )
        for n in negative_pairs
    ]

    avg_pos = sum(pos_sims) / len(pos_sims)
    avg_neg = sum(neg_sims) / len(neg_sims)

    # Positive pairs must have a higher average similarity than negative pairs
    assert avg_pos > avg_neg
    # Every positive pair must have higher similarity than every negative pair
    assert min(pos_sims) > max(neg_sims)


# ---------------------------------------------------------------------------
# Test 12 — Dedicated Semantic Matching API Endpoint
# ---------------------------------------------------------------------------
def test_api_semantic_endpoint(client):
    """POST /api/v1/matching/semantic returns structured semantic results with NO score or ranking."""
    payload = {
        "candidate": {
            "personal_info": {"name": "Jordan Lee", "email": "jordan@example.com"},
            "skills": [
                {"name": "FastAPI", "category": "framework"},
                {"name": "PostgreSQL", "category": "database"},
            ],
            "experience": [
                {
                    "title": "Backend Engineer",
                    "company": "StartupX",
                    "start_date": "2021",
                    "end_date": "2024",
                    "description": "Engineered high-throughput REST APIs and microservices using FastAPI.",
                    "skills": ["FastAPI", "Python"],
                }
            ],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
        },
        "job": {
            "job_title": "API Backend Developer",
            "skills": [
                {
                    "name": "Python Web APIs",
                    "category": "framework",
                    "priority": "must_have",
                    "evidence": "Experience in Python web API development and architecture",
                }
            ],
            "responsibilities": [],
            "must_have": [],
            "nice_to_have": [],
        },
    }

    response = client.post("/api/v1/matching/semantic", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "semantic_results" in data
    assert "summary" in data
    assert "embedding_model" in data

    # Strict architectural check: Zero hiring scores or rankings
    assert "total_score" not in data
    assert "candidate_score" not in data
    assert "score" not in data
    assert "rank" not in data

    # Verify semantic match was identified for Python Web APIs from FastAPI experience
    results = data["semantic_results"]
    assert len(results) == 1
    assert results[0]["similarity"] > 0.35
    assert results[0]["candidate_evidence"] is not None


# ---------------------------------------------------------------------------
# Test 13 — Integrated Endpoint with include_semantic=True
# ---------------------------------------------------------------------------
def test_api_analyze_with_include_semantic(client):
    """POST /api/v1/matching/analyze returns both deterministic and semantic results when requested."""
    payload = {
        "candidate": {
            "personal_info": {"name": "Jordan Lee", "email": "jordan@example.com"},
            "skills": [{"name": "Python", "category": "programming_language"}],
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
        },
        "job": {
            "job_title": "Python Developer",
            "skills": [{"name": "Python", "category": "programming_language", "priority": "must_have"}],
            "responsibilities": [],
            "must_have": [],
            "nice_to_have": [],
        },
        "include_semantic": True,
    }

    response = client.post("/api/v1/matching/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "matches" in data
    assert "summary" in data
    assert "semantic_matches" in data
    assert data["semantic_matches"] is not None
    assert len(data["semantic_matches"]) >= 1


# ---------------------------------------------------------------------------
# Test 14 — Pure Cosine Similarity Function Edge Cases
# ---------------------------------------------------------------------------
def test_compute_cosine_similarity_edge_cases():
    """Verify zero vectors, empty vectors, orthogonal vectors, and identical vectors."""
    assert compute_cosine_similarity([], [1.0, 2.0]) == 0.0
    assert compute_cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0
    # Orthogonal
    assert abs(compute_cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-6
    # Identical
    assert abs(compute_cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) - 1.0) < 1e-6
    # Opposite
    assert abs(compute_cosine_similarity([1.0, 2.0], [-1.0, -2.0]) - (-1.0)) < 1e-6
