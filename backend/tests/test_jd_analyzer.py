import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas import (
    JobProfile,
    JobSkillRequirement,
    JobExperienceRequirement,
    JobEducationRequirement,
    JobCertificationRequirement,
    JobOtherRequirement,
    JobRequirementItem,
)
from backend.app.services.jd_rule_extractor import (
    extract_jd_sections,
    detect_priority,
    extract_experience_requirements,
    extract_education_requirements,
    extract_certification_requirements,
    extract_skill_requirements,
    extract_responsibilities,
    extract_other_requirements,
    parse_job_profile_rules,
)
from backend.app.services.jd_analyzer import analyze_job_description, reconcile_job_profile
from backend.app.ai.llm_client import MockLLMClient

SAMPLE_JD_DIR = Path(__file__).parent.parent.parent / "data" / "sample" / "job_descriptions"


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# 1. Pydantic Schema Validation Tests
# =====================================================================

def test_job_profile_schema_instantiation():
    profile = JobProfile(
        job_title="Backend Engineer",
        company="CloudNexus",
        skills=[
            JobSkillRequirement(name="Python", category="programming_language", priority="must_have"),
            JobSkillRequirement(name="AWS", category="cloud", priority="nice_to_have"),
        ],
        experience_requirements=[
            JobExperienceRequirement(skill="Python", minimum_years=3.0, priority="must_have", text="3+ years of Python")
        ],
        education_requirements=[
            JobEducationRequirement(degree="Bachelor's", field="Computer Science", priority="must_have")
        ],
        certification_requirements=[
            JobCertificationRequirement(name="AWS Certified Solutions Architect", priority="nice_to_have")
        ],
        responsibilities=["Design APIs", "Review code"],
    )
    assert profile.job_title == "Backend Engineer"
    assert len(profile.skills) == 2
    assert profile.skills[0].priority == "must_have"
    assert profile.skills[1].priority == "nice_to_have"
    assert profile.experience_requirements[0].minimum_years == 3.0


def test_job_skill_requirement_sanitization():
    # Invalid category defaults to 'other'
    skill = JobSkillRequirement(name="Git", category="non_existent_category", priority="must_have")
    assert skill.category == "other"

    # Variations of preferred map to nice_to_have
    skill2 = JobSkillRequirement(name="Docker", category="devops", priority="is_a_plus")
    assert skill2.priority == "nice_to_have"


def test_job_requirement_item_unified_model():
    item = JobRequirementItem(
        text="3+ years of Python backend development",
        type="experience",
        priority="must_have",
        skill="Python",
        minimum_years=3.0,
        evidence="3+ years of Python backend development",
    )
    assert item.type == "experience"
    assert item.priority == "must_have"
    assert item.minimum_years == 3.0


# =====================================================================
# 2. Deterministic Rule Extractor Unit Tests
# =====================================================================

def test_extract_jd_sections():
    jd_text = (
        "Job Title: Senior Backend Engineer\n\n"
        "About the Role:\n"
        "We are looking for a backend engineer.\n\n"
        "Responsibilities:\n"
        "- Build APIs\n"
        "- Maintain databases\n\n"
        "Requirements:\n"
        "- 3+ years of Python\n"
        "- PostgreSQL experience\n\n"
        "Nice to Have:\n"
        "- AWS knowledge is a plus\n"
    )
    sections = extract_jd_sections(jd_text)
    assert "summary" in sections
    assert "responsibilities" in sections
    assert "mandatory_requirements" in sections
    assert "preferred_requirements" in sections
    assert "Build APIs" in sections["responsibilities"]
    assert "3+ years of Python" in sections["mandatory_requirements"]


def test_detect_priority_explicit_phrasing():
    assert detect_priority("Experience with AWS is a plus", default_priority="must_have") == "nice_to_have"
    assert detect_priority("Knowledge of Docker is preferred", default_priority="must_have") == "nice_to_have"
    assert detect_priority("Bonus points for GraphQL experience", default_priority="must_have") == "nice_to_have"
    assert detect_priority("Must have 4+ years of Python", default_priority="nice_to_have") == "must_have"
    assert detect_priority("PostgreSQL proficiency is required", default_priority="nice_to_have") == "must_have"
    assert detect_priority("Python programming", default_priority="must_have") == "must_have"


def test_extract_experience_requirements_general_and_skill():
    text = (
        "Requirements:\n"
        "- 5+ years of software development experience\n"
        "- 3+ years of hands-on experience with Python\n"
        "- At least 2 years working with AWS\n"
    )
    sections = extract_jd_sections(text)
    exps = extract_experience_requirements(text, sections)

    assert len(exps) == 3
    # General software experience has skill=None
    assert exps[0]["skill"] is None
    assert exps[0]["minimum_years"] == 5.0

    # Python experience has skill='Python'
    assert exps[1]["skill"] == "Python"
    assert exps[1]["minimum_years"] == 3.0

    # AWS experience has skill='Aws' or 'AWS'
    assert exps[2]["minimum_years"] == 2.0


def test_extract_education_requirements_and_zero_hallucination():
    text_with_degree = (
        "Requirements:\n"
        "- Bachelor's degree in Computer Science or related technical field\n"
        "- Master's degree in Artificial Intelligence preferred\n"
    )
    sections = extract_jd_sections(text_with_degree)
    edus = extract_education_requirements(text_with_degree, sections)

    assert len(edus) == 2
    assert "Bachelor" in edus[0]["degree"]
    assert edus[0]["priority"] == "must_have"
    assert "Master" in edus[1]["degree"]
    assert edus[1]["priority"] == "nice_to_have"

    # JD without degree mentioned
    text_no_degree = (
        "Requirements:\n"
        "- 3+ years of Python\n"
        "- Git proficiency\n"
    )
    sections_no_deg = extract_jd_sections(text_no_degree)
    edus_no_deg = extract_education_requirements(text_no_degree, sections_no_deg)
    assert len(edus_no_deg) == 0  # Zero hallucination


def test_extract_certification_requirements():
    text = (
        "Qualifications:\n"
        "- AWS Certified Solutions Architect preferred\n"
        "- CISSP certification is a plus\n"
    )
    sections = extract_jd_sections(text)
    certs = extract_certification_requirements(text, sections)
    assert len(certs) == 2
    cert_names = [c["name"] for c in certs]
    assert any("AWS Certified" in name for name in cert_names)
    assert any("CISSP" in name for name in cert_names)


def test_extract_responsibilities_isolation():
    text = (
        "Responsibilities:\n"
        "- Design high-throughput REST APIs\n"
        "- Architect PostgreSQL database schemas\n"
        "- Conduct peer code reviews\n\n"
        "Requirements:\n"
        "- Python\n"
    )
    sections = extract_jd_sections(text)
    resps = extract_responsibilities(sections)
    assert len(resps) == 3
    assert "Design high-throughput REST APIs" in resps
    assert "Conduct peer code reviews" in resps


def test_extract_other_requirements():
    text = (
        "Requirements:\n"
        "- Must be authorized to work in the US or India\n"
        "- Fluent in English with strong written and verbal communication\n"
        "- Willingness to work night shifts\n"
    )
    sections = extract_jd_sections(text)
    others = extract_other_requirements(text, sections)
    assert len(others) >= 2
    types = [o["type"] for o in others]
    assert "location" in types or "language" in types or "other" in types


# =====================================================================
# 3. Service-Level Extraction Tests with Mock LLM
# =====================================================================

@pytest.mark.asyncio
async def test_analyze_job_description_service():
    jd_path = SAMPLE_JD_DIR / "backend_engineer_jd.txt"
    assert jd_path.exists(), f"Sample JD not found: {jd_path}"
    raw_text = jd_path.read_text(encoding="utf-8")

    mock_client = MockLLMClient()
    profile = await analyze_job_description(raw_text, llm_client=mock_client)

    assert profile.job_title == "Senior Backend Software Engineer"
    assert profile.company == "CloudNexus"
    assert len(profile.skills) > 0

    # Verify skill priorities
    skill_dict = {s.name: s.priority for s in profile.skills}
    assert skill_dict.get("Python") == "must_have"
    assert skill_dict.get("FastAPI") == "must_have"
    assert skill_dict.get("AWS") == "nice_to_have"
    assert skill_dict.get("Docker") == "nice_to_have"

    # Verify experience requirements
    assert len(profile.experience_requirements) >= 2
    assert any(e.minimum_years == 4.0 for e in profile.experience_requirements)

    # Verify education
    assert len(profile.education_requirements) >= 1
    assert any("Bachelor" in (ed.degree or "") for ed in profile.education_requirements)

    # Verify must_have and nice_to_have collections
    assert len(profile.must_have) > 0
    assert len(profile.nice_to_have) > 0
    assert all(item.priority == "must_have" for item in profile.must_have)
    assert all(item.priority == "nice_to_have" for item in profile.nice_to_have)


@pytest.mark.asyncio
async def test_reconciliation_overrides_false_must_have():
    raw_text = (
        "Job Title: Python Developer\n\n"
        "Requirements:\n"
        "- Python required\n\n"
        "Preferred:\n"
        "- Experience with AWS is a plus\n"
    )
    # Simulated flawed LLM output marking AWS as must_have despite text saying "is a plus"
    flawed_profile = JobProfile(
        job_title="Python Developer",
        skills=[
            JobSkillRequirement(name="Python", category="programming_language", priority="must_have"),
            JobSkillRequirement(name="AWS", category="cloud", priority="must_have", evidence="Experience with AWS is a plus"),
        ],
    )
    sections = extract_jd_sections(raw_text)
    rule_data = parse_job_profile_rules(raw_text)

    reconciled = reconcile_job_profile(flawed_profile, raw_text, sections, rule_data)
    aws_skill = next(s for s in reconciled.skills if s.name == "AWS")
    assert aws_skill.priority == "nice_to_have"


# =====================================================================
# 4. API Endpoint Tests: POST /api/v1/jobs/analyze
# =====================================================================

def test_api_analyze_job_text_json(client):
    payload = {
        "job_description": (
            "Job Title: Frontend Engineer\n"
            "Company: PixelCraft\n\n"
            "Responsibilities:\n"
            "- Build React apps\n\n"
            "Requirements:\n"
            "- 2+ years of React and TypeScript\n"
            "- HTML5 and CSS3\n\n"
            "Nice to have:\n"
            "- Next.js is a plus\n"
        ),
        "job_title": "Frontend Engineer",
    }
    response = client.post("/api/v1/jobs/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["job_title"] == "Frontend Engineer"
    assert data["metadata"]["source_type"] == "text"
    profile = data["profile"]
    assert len(profile["skills"]) >= 2
    assert len(profile["responsibilities"]) == 1
    assert any(s["name"] == "React" for s in profile["skills"])


def test_api_analyze_job_empty_text(client):
    response = client.post("/api/v1/jobs/analyze", json={"job_description": "   "})
    assert response.status_code == 422 or response.status_code == 400


# =====================================================================
# 5. API Endpoint Tests: POST /api/v1/jobs/analyze/upload
# =====================================================================

def test_api_analyze_job_pdf_upload(client):
    pdf_path = SAMPLE_JD_DIR / "backend_engineer_jd.pdf"
    assert pdf_path.exists(), f"Sample PDF not found: {pdf_path}"

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/v1/jobs/analyze/upload",
        files={"file": ("backend_engineer_jd.pdf", file_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["metadata"]["source_type"] == "pdf"
    profile = data["profile"]
    assert profile["job_title"] == "Senior Backend Software Engineer"
    assert len(profile["skills"]) > 0
    assert len(profile["experience_requirements"]) > 0


def test_api_analyze_job_docx_upload(client):
    docx_path = SAMPLE_JD_DIR / "frontend_developer_jd.docx"
    assert docx_path.exists(), f"Sample DOCX not found: {docx_path}"

    with open(docx_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/v1/jobs/analyze/upload",
        files={"file": ("frontend_developer_jd.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["metadata"]["source_type"] == "docx"
    profile = data["profile"]
    assert profile["job_title"] == "Frontend React Developer"
    assert len(profile["skills"]) > 0


def test_api_analyze_job_unsupported_format(client):
    response = client.post(
        "/api/v1/jobs/analyze/upload",
        files={"file": ("test.png", b"fake-png-content", "image/png")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_api_analyze_job_scanned_pdf(client):
    import pymupdf
    doc = pymupdf.open()
    doc.new_page()
    blank_bytes = doc.tobytes()
    doc.close()

    response = client.post(
        "/api/v1/jobs/analyze/upload",
        files={"file": ("blank.pdf", blank_bytes, "application/pdf")},
    )
    assert response.status_code == 422
    assert "scanned" in response.json()["detail"].lower()
