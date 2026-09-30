"""
Test suite for Phase 5: Skill Normalization & Taxonomy Mapping.

Validates:
1. Basic case and whitespace normalization.
2. Canonical alias resolution (JS, TS, Postgres, GCP, K8s, NLP, ML, etc.).
3. Version stripping (Python 3.11, React 18, etc.).
4. Punctuation sensitivity (C++ vs C, C# vs C, .NET vs Node.js).
5. Unknown skill handling (zero hallucination, preserved text, method="unknown").
6. Authoritative category mapping from taxonomy.
7. Candidate skill deduplication and provenance tracking.
8. Job description skill requirement deduplication (priority, min_years, evidence).
9. False positive word protection.
10. Integration with CandidateProfile and JobProfile pipelines.
11. REST API endpoints (/api/v1/skills/normalize and /api/v1/skills/taxonomy).
12. E2E normalization across all 4 synthetic resumes and 4 synthetic JDs.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas import (
    SkillItem,
    JobSkillRequirement,
    NormalizedSkill,
    NormalizedJobSkill,
)
from backend.app.services.skill_taxonomy import (
    lookup_canonical_skill,
    get_all_canonical_skills,
    get_taxonomy_categories,
    CANONICAL_SKILL_REGISTRY,
)
from backend.app.services.skill_normalizer import (
    clean_skill_string,
    is_false_positive_skill,
    normalize_skill,
    normalize_candidate_skills,
    normalize_job_skills,
)
from backend.app.services.resume_extractor import extract_candidate_profile
from backend.app.services.jd_analyzer import analyze_job_description
from backend.app.services.document_parser import parse_document

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Basic Normalization Tests
# ---------------------------------------------------------------------------
def test_clean_skill_string():
    assert clean_skill_string("  Python  ") == "Python"
    assert clean_skill_string("- Python") == "Python"
    assert clean_skill_string("•   Machine   Learning  ") == "Machine Learning"
    assert clean_skill_string("1. FastAPI,") == "FastAPI"
    # Preserves meaningful technical symbols
    assert clean_skill_string("C++") == "C++"
    assert clean_skill_string("C#") == "C#"
    assert clean_skill_string(".NET") == ".NET"
    assert clean_skill_string("Node.js") == "Node.js"
    assert clean_skill_string("CI/CD") == "CI/CD"


def test_basic_case_and_casing_normalization():
    cases = ["Python", "python", "PYTHON", "  pYtHoN  "]
    for case in cases:
        norm = normalize_skill(case)
        assert norm is not None
        assert norm.canonical_name == "Python"
        assert norm.category == "programming_language"
        assert norm.confidence == 1.0


# ---------------------------------------------------------------------------
# 2. Alias Mapping Tests
# ---------------------------------------------------------------------------
def test_safe_alias_mappings():
    alias_expectations = {
        "JS": ("JavaScript", "programming_language"),
        "js": ("JavaScript", "programming_language"),
        "ECMAScript": ("JavaScript", "programming_language"),
        "TS": ("TypeScript", "programming_language"),
        "ts": ("TypeScript", "programming_language"),
        "Py": ("Python", "programming_language"),
        "Postgres": ("PostgreSQL", "database"),
        "postgres db": ("PostgreSQL", "database"),
        "pgsql": ("PostgreSQL", "database"),
        "GCP": ("Google Cloud", "cloud"),
        "google cloud platform": ("Google Cloud", "cloud"),
        "K8s": ("Kubernetes", "devops"),
        "k8": ("Kubernetes", "devops"),
        "NLP": ("Natural Language Processing", "ai_ml"),
        "ML": ("Machine Learning", "ai_ml"),
        "DL": ("Deep Learning", "ai_ml"),
        "LLM": ("Large Language Models", "ai_ml"),
        "AWS": ("AWS", "cloud"),
        "amazon web services": ("AWS", "cloud"),
        "sklearn": ("Scikit-Learn", "library"),
        "scikit learn": ("Scikit-Learn", "library"),
        "cicd": ("CI/CD", "devops"),
        "restful api": ("REST APIs", "other"),
        "rest": ("REST APIs", "other"),
    }

    for alias, (expected_canonical, expected_cat) in alias_expectations.items():
        norm = normalize_skill(alias)
        assert norm is not None, f"Failed for alias: {alias}"
        assert norm.canonical_name == expected_canonical, f"Failed for alias: {alias}"
        assert norm.category == expected_cat, f"Category mismatch for alias: {alias}"
        assert norm.normalization_method in {"exact", "case_normalized", "alias"}


# ---------------------------------------------------------------------------
# 3. Version Stripping Tests
# ---------------------------------------------------------------------------
def test_version_normalization():
    version_cases = {
        "Python 3": "Python",
        "Python 3.11": "Python",
        "Python 3.x": "Python",
        "React 18": "React",
        "React.js": "React",
        "Postgres 15": "PostgreSQL",
        "PostgreSQL 14": "PostgreSQL",
        "Java 17": "Java",
        "Java 8": "Java",
        "Vue 3": "Vue.js",
        "Angular 2+": "Angular",
    }

    for raw, expected_canonical in version_cases.items():
        norm = normalize_skill(raw)
        assert norm is not None, f"Failed for version string: {raw}"
        assert norm.canonical_name == expected_canonical, f"Failed for: {raw}"
        assert norm.normalization_method in {"exact", "case_normalized", "alias", "version_stripped"}


# ---------------------------------------------------------------------------
# 4. Punctuation Sensitivity Tests (Crucial Section 8 & 10)
# ---------------------------------------------------------------------------
def test_punctuation_sensitive_skills_separation():
    # C++ vs C vs C#
    c_norm = normalize_skill("C")
    cpp_norm = normalize_skill("C++")
    csharp_norm = normalize_skill("C#")

    assert c_norm is not None and c_norm.canonical_name == "C"
    assert cpp_norm is not None and cpp_norm.canonical_name == "C++"
    assert csharp_norm is not None and csharp_norm.canonical_name == "C#"
    assert c_norm.canonical_name != cpp_norm.canonical_name
    assert c_norm.canonical_name != csharp_norm.canonical_name
    assert cpp_norm.canonical_name != csharp_norm.canonical_name

    # Spaced variations
    cpp_spaced = normalize_skill("c ++")
    csharp_spaced = normalize_skill("c #")
    assert cpp_spaced is not None and cpp_spaced.canonical_name == "C++"
    assert csharp_spaced is not None and csharp_spaced.canonical_name == "C#"

    # .NET vs Node.js vs Next.js
    dotnet_norm = normalize_skill(".NET")
    node_norm = normalize_skill("Node.js")
    next_norm = normalize_skill("Next.js")

    assert dotnet_norm is not None and dotnet_norm.canonical_name == ".NET"
    assert node_norm is not None and node_norm.canonical_name == "Node.js"
    assert next_norm is not None and next_norm.canonical_name == "Next.js"
    assert dotnet_norm.canonical_name != node_norm.canonical_name
    assert node_norm.canonical_name != next_norm.canonical_name


# ---------------------------------------------------------------------------
# 5. Unknown Skill Handling Tests
# ---------------------------------------------------------------------------
def test_unknown_skill_zero_hallucination():
    raw_unknown = "CustomInternalGraphEngine"
    norm = normalize_skill(raw_unknown, hint_category="tool")

    assert norm is not None
    assert norm.canonical_name == "CustomInternalGraphEngine"
    assert norm.original_name == raw_unknown
    assert norm.category == "tool"  # Kept hint category
    assert norm.normalization_method == "unknown"
    assert norm.confidence == 0.5

    # If no valid hint, defaults to "other"
    norm_no_hint = normalize_skill("NovelProprietaryAlgo")
    assert norm_no_hint is not None
    assert norm_no_hint.canonical_name == "NovelProprietaryAlgo"
    assert norm_no_hint.category == "other"
    assert norm_no_hint.normalization_method == "unknown"


# ---------------------------------------------------------------------------
# 6. Authoritative Category Consistency Tests
# ---------------------------------------------------------------------------
def test_category_consistency_from_registry():
    # Even if extracted profile passed category="other" for Python, registry overrides
    norm_python = normalize_skill("Python", hint_category="other")
    assert norm_python is not None
    assert norm_python.category == "programming_language"

    norm_fastapi = normalize_skill("FastAPI", hint_category="tool")
    assert norm_fastapi is not None
    assert norm_fastapi.category == "framework"

    norm_postgres = normalize_skill("PostgreSQL", hint_category="cloud")
    assert norm_postgres is not None
    assert norm_postgres.category == "database"

    norm_docker = normalize_skill("Docker", hint_category="other")
    assert norm_docker is not None
    assert norm_docker.category == "devops"

    norm_aws = normalize_skill("AWS", hint_category="database")
    assert norm_aws is not None
    assert norm_aws.category == "cloud"

    norm_rest = normalize_skill("REST APIs", hint_category="programming_language")
    assert norm_rest is not None
    assert norm_rest.category == "other"


# ---------------------------------------------------------------------------
# 7. False Positive Word Protection Tests
# ---------------------------------------------------------------------------
def test_false_positive_protection():
    stopwords = [
        "experience",
        "work",
        "team",
        "development",
        "data",
        "model",
        "code",
        "skills",
        "years",
        "engineer",
        "responsibilities",
        "strong",
        "good",
    ]
    for word in stopwords:
        assert is_false_positive_skill(word) is True
        assert normalize_skill(word) is None


# ---------------------------------------------------------------------------
# 8. Candidate Skill Deduplication & Provenance Tests
# ---------------------------------------------------------------------------
def test_candidate_skill_deduplication():
    raw_skills = [
        SkillItem(name="Python", category="programming_language"),
        SkillItem(name="python", category="other"),
        SkillItem(name="Python 3", category="programming_language"),
        SkillItem(name="FastAPI", category="framework"),
        SkillItem(name="fastapi", category="other"),
        SkillItem(name="K8s", category="devops"),
        SkillItem(name="Kubernetes", category="devops"),
    ]

    normalized = normalize_candidate_skills(raw_skills)

    # 7 input skills should deduplicate into 3 canonical skills: Python, FastAPI, Kubernetes
    assert len(normalized) == 3

    names = {s.canonical_name: s for s in normalized}
    assert "Python" in names
    assert "FastAPI" in names
    assert "Kubernetes" in names

    # Verify provenance (original_names)
    python_skill = names["Python"]
    assert python_skill.category == "programming_language"
    assert python_skill.original_names == ["Python", "python", "Python 3"]

    k8s_skill = names["Kubernetes"]
    assert k8s_skill.category == "devops"
    assert k8s_skill.original_names == ["K8s", "Kubernetes"]


# ---------------------------------------------------------------------------
# 9. Job Description Skill Deduplication Tests
# ---------------------------------------------------------------------------
def test_job_skill_deduplication_precedence():
    jd_skills = [
        JobSkillRequirement(
            name="Python",
            category="programming_language",
            priority="must_have",
            minimum_years=5.0,
            evidence="5+ years of Python experience required.",
        ),
        JobSkillRequirement(
            name="Python 3",
            category="other",
            priority="nice_to_have",
            minimum_years=3.0,
            evidence="Experience with Python 3 is a plus.",
        ),
        JobSkillRequirement(
            name="NLP",
            category="ai_ml",
            priority="nice_to_have",
            minimum_years=None,
            evidence="NLP experience preferred.",
        ),
        JobSkillRequirement(
            name="Natural Language Processing",
            category="ai_ml",
            priority="must_have",
            minimum_years=2.0,
            evidence="Must have 2+ years of Natural Language Processing.",
        ),
    ]

    normalized = normalize_job_skills(jd_skills)
    assert len(normalized) == 2

    job_map = {s.canonical_name: s for s in normalized}

    # Python check: must_have wins, max years (5.0) wins
    python_req = job_map["Python"]
    assert python_req.priority == "must_have"
    assert python_req.minimum_years == 5.0
    assert "Python" in python_req.original_names
    assert "Python 3" in python_req.original_names
    assert "5+ years" in python_req.evidence
    assert "is a plus" in python_req.evidence

    # NLP check: Natural Language Processing canonical name, must_have wins, 2.0 years
    nlp_req = job_map["Natural Language Processing"]
    assert nlp_req.priority == "must_have"
    assert nlp_req.minimum_years == 2.0
    assert nlp_req.original_names == ["NLP", "Natural Language Processing"]


# ---------------------------------------------------------------------------
# 10. Pipeline Integration Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_candidate_profile_pipeline_populates_normalized_skills():
    resume_text = (
        "Alice Smith\n"
        "alex.smith@example.com\n"
        "+1 555-123-4567\n"
        "Skills: Python, python, Python 3.11, JS, React 18, Postgres, Docker\n"
        "Experience: 4 years as a Backend Engineer at CloudTech.\n"
        "Education: B.S. in Computer Science from State University.\n"
    )

    profile = await extract_candidate_profile(resume_text)

    # Original skills preserved
    assert len(profile.skills) > 0
    # Normalized skills populated
    assert len(profile.normalized_skills) > 0

    norm_names = {s.canonical_name for s in profile.normalized_skills}
    assert "Python" in norm_names
    assert "JavaScript" in norm_names  # JS normalized to JavaScript
    assert "React" in norm_names       # React 18 normalized to React
    assert "PostgreSQL" in norm_names  # Postgres normalized to PostgreSQL
    assert "Docker" in norm_names

    # Check that Python was normalized properly
    python_norm = next(s for s in profile.normalized_skills if s.canonical_name == "Python")
    assert len(python_norm.original_names) >= 1
    assert python_norm.category == "programming_language"


@pytest.mark.asyncio
async def test_job_profile_pipeline_populates_normalized_skills():
    jd_text = (
        "Role: Senior Full Stack Developer\n"
        "Requirements:\n"
        "- 5+ years of experience with Python and FastAPI.\n"
        "- Experience with Postgres and GCP is a plus.\n"
        "- Bachelor's degree in Computer Science.\n"
    )

    profile = await analyze_job_description(jd_text)

    # Original skills preserved
    assert len(profile.skills) > 0
    # Normalized skills populated
    assert len(profile.normalized_skills) > 0

    norm_map = {s.canonical_name: s for s in profile.normalized_skills}
    assert "Python" in norm_map
    assert "FastAPI" in norm_map
    assert "PostgreSQL" in norm_map   # Postgres normalized to PostgreSQL
    assert "Google Cloud" in norm_map # GCP normalized to Google Cloud

    assert norm_map["Python"].priority == "must_have"
    assert norm_map["Google Cloud"].priority == "nice_to_have"


# ---------------------------------------------------------------------------
# 11. REST API Endpoints Tests
# ---------------------------------------------------------------------------
def test_api_normalize_skills_endpoint():
    payload = {
        "skills": ["py", "python", "Python 3.11", "js", "Postgres", "k8s", "Docker", "NovelFrameworkX"],
        "source": "api_test",
    }
    response = client.post("/api/v1/skills/normalize", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["count"] > 0
    canonical_names = [s["canonical_name"] for s in data["normalized_skills"]]
    assert "Python" in canonical_names
    assert "JavaScript" in canonical_names
    assert "PostgreSQL" in canonical_names
    assert "Kubernetes" in canonical_names
    assert "Docker" in canonical_names
    assert "NovelFrameworkX" in canonical_names

    # Unknown skill properties
    unknown_item = next(s for s in data["normalized_skills"] if s["canonical_name"] == "NovelFrameworkX")
    assert unknown_item["normalization_method"] == "unknown"
    assert unknown_item["confidence"] == 0.5


def test_api_taxonomy_endpoint():
    response = client.get("/api/v1/skills/taxonomy")
    assert response.status_code == 200
    data = response.json()

    assert "categories" in data
    assert "programming_language" in data["categories"]
    assert "cloud" in data["categories"]
    assert data["canonical_skills_count"] > 50
    assert "Python" in data["skills"]
    assert "Docker" in data["skills"]


# ---------------------------------------------------------------------------
# 12. E2E Tests on Synthetic Resumes & JDs
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_e2e_synthetic_resumes_normalization():
    resume_files = [
        "data/sample/resumes/synthetic_software_engineer.pdf",
        "data/sample/resumes/synthetic_frontend_developer.docx",
        "data/sample/resumes/synthetic_data_scientist.pdf",
        "data/sample/resumes/synthetic_junior_intern.docx",
    ]

    for rf in resume_files:
        with open(rf, "rb") as fp:
            doc = parse_document(fp.read(), rf)
        profile = await extract_candidate_profile(doc.text)

        assert len(profile.normalized_skills) > 0
        canonical_set = {s.canonical_name for s in profile.normalized_skills}

        # Check key technology canonical representations
        if "software_engineer" in rf:
            assert "Python" in canonical_set
            assert "PostgreSQL" in canonical_set
            assert "Docker" in canonical_set
            assert "Kubernetes" in canonical_set
        elif "frontend_developer" in rf:
            assert "JavaScript" in canonical_set
            assert "TypeScript" in canonical_set
            assert "React" in canonical_set
            assert "Next.js" in canonical_set
        elif "data_scientist" in rf:
            assert "Python" in canonical_set
            assert "PyTorch" in canonical_set
            assert "Machine Learning" in canonical_set
            assert "Natural Language Processing" in canonical_set  # NLP -> Natural Language Processing
        elif "junior_intern" in rf:
            assert "Python" in canonical_set
            assert "C" in canonical_set
            assert "Java" in canonical_set
            assert "Git" in canonical_set


@pytest.mark.asyncio
async def test_e2e_synthetic_jds_normalization():
    jd_files = [
        "data/sample/job_descriptions/backend_engineer_jd.txt",
        "data/sample/job_descriptions/frontend_developer_jd.txt",
        "data/sample/job_descriptions/data_scientist_jd.txt",
        "data/sample/job_descriptions/entry_level_intern_jd.txt",
    ]

    for jf in jd_files:
        with open(jf, "r", encoding="utf-8") as fp:
            text = fp.read()
        profile = await analyze_job_description(text)

        assert len(profile.normalized_skills) > 0
        canonical_map = {s.canonical_name: s for s in profile.normalized_skills}

        if "backend_engineer" in jf:
            assert "Python" in canonical_map
            assert canonical_map["Python"].priority == "must_have"
            assert "FastAPI" in canonical_map
            assert "Docker" in canonical_map
        elif "frontend_developer" in jf:
            assert "React" in canonical_map
            assert "TypeScript" in canonical_map
            assert "Next.js" in canonical_map
        elif "data_scientist" in jf:
            assert "Python" in canonical_map
            # In data_scientist_jd, both NLP and Natural Language Processing appeared;
            # they must have been deduplicated into ONE Natural Language Processing skill!
            assert "Natural Language Processing" in canonical_map
            assert "NLP" not in canonical_map  # Alias merged
            assert len(canonical_map["Natural Language Processing"].original_names) >= 2
        elif "entry_level_intern" in jf:
            assert "Python" in canonical_map
            assert "C" in canonical_map
            assert "Java" in canonical_map
