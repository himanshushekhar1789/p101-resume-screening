import io
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas import (
    CandidateProfile,
    PersonalInfo,
    SkillItem,
    EducationItem,
    ExperienceItem,
    ProjectItem,
    CertificationItem,
    AchievementItem,
)
from backend.app.services.rule_extractor import (
    extract_email,
    extract_phone,
    extract_links,
    extract_sections,
)
from backend.app.ai.llm_client import MockLLMClient
from backend.app.ai.validators import validate_llm_json, LLMValidationError, extract_json_payload
from backend.app.services.resume_extractor import extract_candidate_profile

SAMPLE_DIR = Path(__file__).parent.parent.parent / "data" / "sample" / "resumes"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# =====================================================================
# 1. Schema Validation Tests
# =====================================================================

def test_candidate_profile_valid():
    profile = CandidateProfile(
        personal_info=PersonalInfo(
            name="John Tester",
            email="john.tester@example.com",
            phone="+1 555-123-4567",
            github_url="https://github.com/johntester",
        ),
        summary="Experienced engineer with backend skills.",
        skills=[SkillItem(name="Python", category="programming_language")],
        education=[EducationItem(degree="B.S. in CS", institution="MIT", end_year=2022)],
        experience=[
            ExperienceItem(
                title="Software Engineer",
                company="TechCorp",
                start_date="2022-01",
                is_current=True,
                skills=["Python", "FastAPI"],
            )
        ],
        projects=[
            ProjectItem(
                name="Resume Screener",
                description="AI-assisted system",
                technologies=["Python", "FastAPI"],
            )
        ],
    )
    assert profile.personal_info.name == "John Tester"
    assert profile.personal_info.email == "john.tester@example.com"
    assert profile.personal_info.phone == "+1 555-123-4567"
    assert len(profile.skills) == 1
    assert profile.skills[0].name == "Python"
    assert profile.experience[0].is_current is True


def test_candidate_profile_missing_optional_fields():
    # Only empty profile without crash
    profile = CandidateProfile()
    assert profile.personal_info.name is None
    assert profile.personal_info.email is None
    assert profile.summary is None
    assert profile.skills == []
    assert profile.education == []
    assert profile.experience == []
    assert profile.projects == []


def test_candidate_profile_invalid_email():
    with pytest.raises(ValueError, match="Invalid email address format"):
        PersonalInfo(email="not-an-email-address")


def test_candidate_profile_phone_string_conversion():
    # If phone is provided as an integer, it must be validated/converted to string
    info = PersonalInfo(phone=9876543210)
    assert info.phone == "9876543210"
    assert isinstance(info.phone, str)


# =====================================================================
# 2. Deterministic Rule Extraction Tests
# =====================================================================

def test_extract_email():
    text = "Reach me at test.user+dev@example-school.edu for questions."
    assert extract_email(text) == "test.user+dev@example-school.edu"

    text_no_email = "No contact details provided."
    assert extract_email(text_no_email) is None


def test_extract_phone():
    text_us = "Call (555) 345-6789 or email me."
    assert extract_phone(text_us) == "(555) 345-6789"

    text_intl = "Tel: +1-555-234-5678."
    assert extract_phone(text_intl) is not None

    text_none = "No phone number listed here."
    assert extract_phone(text_none) is None


def test_extract_links():
    text = (
        "Check my code: https://github.com/davidvance and profile: "
        "https://linkedin.com/in/david-vance-dev"
    )
    links = extract_links(text)
    assert links["github_url"] == "https://github.com/davidvance"
    assert links["linkedin_url"] == "https://linkedin.com/in/david-vance-dev"


def test_extract_sections():
    resume_sample = (
        "Alice Walker\nalice@example.com\n\n"
        "Summary\nPassionate engineer.\n\n"
        "Technical Skills\nPython, Docker, SQL\n\n"
        "Work Experience\nEngineer at StartupX\n\n"
        "Education\nB.S. Computer Science\n"
    )
    sections = extract_sections(resume_sample)
    assert "summary" in sections
    assert "Passionate engineer." in sections["summary"]
    assert "skills" in sections
    assert "Python, Docker, SQL" in sections["skills"]
    assert "experience" in sections
    assert "education" in sections


# =====================================================================
# 3. LLM JSON Validation Tests
# =====================================================================

def test_validate_llm_json_clean():
    valid_payload = json.dumps({
        "personal_info": {"name": "Test User", "email": "user@example.com", "phone": "123-456-7890"},
        "summary": "Experienced dev",
        "skills": [{"name": "Python", "category": "programming_language"}],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "achievements": [],
    })
    profile = validate_llm_json(valid_payload, CandidateProfile)
    assert profile.personal_info.name == "Test User"
    assert profile.personal_info.email == "user@example.com"
    assert profile.skills[0].name == "Python"


def test_validate_llm_json_markdown_wrapped():
    markdown_wrapped = (
        "Here is the parsed profile:\n```json\n"
        "{\n"
        '  "personal_info": {"name": "Markdown Dev", "email": "m@example.com", "phone": null},\n'
        '  "summary": null,\n'
        '  "skills": [],\n'
        '  "education": [],\n'
        '  "experience": [],\n'
        '  "projects": [],\n'
        '  "certifications": [],\n'
        '  "achievements": []\n'
        "}\n"
        "```\nHope this helps!"
    )
    profile = validate_llm_json(markdown_wrapped, CandidateProfile)
    assert profile.personal_info.name == "Markdown Dev"
    assert profile.personal_info.email == "m@example.com"


def test_validate_llm_json_malformed():
    malformed = "{ personal_info: { name: 'unquoted key' } "
    with pytest.raises(LLMValidationError, match="could not be parsed as valid JSON"):
        validate_llm_json(malformed, CandidateProfile)


def test_validate_llm_json_schema_error():
    # Invalid email in payload triggers Pydantic schema validation error
    invalid_schema = json.dumps({
        "personal_info": {"name": "Bad Email User", "email": "not-a-valid-email"}
    })
    with pytest.raises(LLMValidationError, match="failed schema validation"):
        validate_llm_json(invalid_schema, CandidateProfile)


# =====================================================================
# 4. Service-Level Extraction Tests with Mock LLM
# =====================================================================

@pytest.mark.asyncio
async def test_extract_candidate_profile_service():
    raw_text = (
        "David Vance\n"
        "Email: david.vance@example-dev.org | Phone: +1 (555) 234-5678\n"
        "LinkedIn: https://linkedin.com/in/david-vance-dev | GitHub: https://github.com/davidvance\n\n"
        "Professional Summary\n"
        "Backend Software Engineer with 5+ years building scalable microservices using Python, FastAPI, and PostgreSQL.\n\n"
        "Technical Skills\n"
        "Python, FastAPI, PostgreSQL, Docker, Git, AWS\n\n"
        "Work Experience\n"
        "Senior Software Engineer - CloudCorp (2022 - Present)\n"
        "Designed high-throughput REST APIs.\n\n"
        "Education\n"
        "B.Tech in Computer Science - State Tech University (2015 - 2019)\n"
    )

    mock_client = MockLLMClient()
    profile = await extract_candidate_profile(raw_text, llm_client=mock_client)

    assert profile.personal_info.name == "David Vance"
    assert profile.personal_info.email == "david.vance@example-dev.org"
    assert profile.personal_info.phone == "+1 (555) 234-5678"
    assert profile.personal_info.linkedin_url == "https://linkedin.com/in/david-vance-dev"
    assert profile.personal_info.github_url == "https://github.com/davidvance"
    assert profile.summary is not None
    skill_names = [s.name for s in profile.skills]
    assert "Python" in skill_names
    assert "FastAPI" in skill_names


# =====================================================================
# 5. API Endpoint Tests: POST /api/v1/resumes/extract
# =====================================================================

def test_api_extract_synthetic_pdf(client):
    pdf_path = SAMPLE_DIR / "synthetic_software_engineer.pdf"
    assert pdf_path.exists(), f"Sample file not found: {pdf_path}"

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/v1/resumes/extract",
        files={"file": ("synthetic_software_engineer.pdf", file_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "synthetic_software_engineer.pdf"
    assert data["file_type"] == "pdf"

    profile = data["profile"]
    assert profile["personal_info"]["name"] == "David Vance"
    assert profile["personal_info"]["email"] == "david.vance@example-dev.org"
    assert len(profile["skills"]) > 0
    assert any(s["name"] == "Python" for s in profile["skills"])
    assert len(profile["education"]) > 0


def test_api_extract_synthetic_docx(client):
    docx_path = SAMPLE_DIR / "synthetic_frontend_developer.docx"
    assert docx_path.exists(), f"Sample file not found: {docx_path}"

    with open(docx_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/v1/resumes/extract",
        files={"file": ("synthetic_frontend_developer.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "synthetic_frontend_developer.docx"
    assert data["file_type"] == "docx"

    profile = data["profile"]
    assert profile["personal_info"]["name"] == "Elena Rostova"
    assert profile["personal_info"]["email"] == "elena.rostova@example-frontend.net"
    assert any(s["name"] in ["React", "TypeScript", "JavaScript"] for s in profile["skills"])


def test_api_extract_unsupported_format(client):
    response = client.post(
        "/api/v1/resumes/extract",
        files={"file": ("test.png", b"fake-png-content", "image/png")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_api_extract_scanned_pdf(client):
    import pymupdf
    doc = pymupdf.open()
    doc.new_page()  # blank page
    blank_bytes = doc.tobytes()
    doc.close()

    response = client.post(
        "/api/v1/resumes/extract",
        files={"file": ("blank.pdf", blank_bytes, "application/pdf")},
    )
    assert response.status_code == 422
    assert "scanned" in response.json()["detail"].lower()


# =====================================================================
# 6. Phase 3.1 Quality Hardening Tests
# =====================================================================

def test_multi_job_experience_separation(client):
    """Verify that multiple experiences are cleanly separated with distinct titles, companies, dates, and duties."""
    pdf_path = SAMPLE_DIR / "synthetic_software_engineer.pdf"
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/v1/resumes/extract",
        files={"file": ("synthetic_software_engineer.pdf", file_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    profile = response.json()["profile"]

    # Must extract both jobs (not merged into one)
    assert len(profile["experience"]) == 2, f"Expected 2 experiences, got {len(profile['experience'])}"

    exp1 = profile["experience"][0]
    exp2 = profile["experience"][1]

    # First role: Senior Software Engineer at CloudCorp
    assert exp1["title"] == "Senior Software Engineer"
    assert exp1["company"] == "CloudCorp"
    assert exp1["is_current"] is True
    assert exp1["start_date"] == "2022"
    assert not exp1["company"].startswith(("-", "*", "•"))

    # Second role: Software Developer at AppLabs
    assert exp2["title"] == "Software Developer"
    assert exp2["company"] == "AppLabs"
    assert exp2["is_current"] is False
    assert exp2["start_date"] == "2019"
    assert exp2["end_date"] == "2022"
    assert not exp2["company"].startswith(("-", "*", "•"))


def test_education_formats_parsing():
    """Verify robust parsing of Education Formats A (multi-line), B (dash-delimited), and C (comma-delimited)."""
    from backend.app.services.rule_extractor import parse_education_blocks

    # Format A: Multi-line
    format_a = (
        "Bachelor of Technology in Computer Science\n"
        "National Institute of Technology\n"
        "2016 - 2020 | CGPA: 8.9/10"
    )
    res_a = parse_education_blocks(format_a)
    assert len(res_a) == 1
    assert res_a[0]["degree"] == "Bachelor of Technology"
    assert res_a[0]["field"] == "Computer Science"
    assert res_a[0]["institution"] == "National Institute of Technology"
    assert res_a[0]["start_year"] == 2016
    assert res_a[0]["end_year"] == 2020

    # Format B: Dash-delimited
    format_b = "M.S. in Artificial Intelligence - Institute of Technology (2018 - 2020)"
    res_b = parse_education_blocks(format_b)
    assert len(res_b) == 1
    assert res_b[0]["degree"] == "M.S."
    assert res_b[0]["field"] == "Artificial Intelligence"
    assert res_b[0]["institution"] == "Institute of Technology"
    assert res_b[0]["start_year"] == 2018
    assert res_b[0]["end_year"] == 2020

    # Format C: Comma-delimited
    format_c = "B.Tech in Computer Science, State Tech University, 2015 - 2019"
    res_c = parse_education_blocks(format_c)
    assert len(res_c) == 1
    assert res_c[0]["degree"] == "B.Tech"
    assert res_c[0]["field"] == "Computer Science"
    assert res_c[0]["institution"] == "State Tech University"
    assert res_c[0]["start_year"] == 2015
    assert res_c[0]["end_year"] == 2019


def test_project_name_description_separation():
    """Verify that project names are cleanly isolated from project descriptions."""
    from backend.app.services.rule_extractor import parse_project_blocks

    text = (
        "- E-Commerce Microservices: Built an API gateway using FastAPI with Docker containerization.\n"
        "- Analytics Dashboard - Real-time metrics visualization with React and Tailwind CSS."
    )
    projs = parse_project_blocks(text)
    assert len(projs) == 2

    assert projs[0]["name"] == "E-Commerce Microservices"
    assert "FastAPI" in projs[0]["description"]
    assert "Fastapi" in projs[0]["technologies"] or "Docker" in projs[0]["technologies"]

    assert projs[1]["name"] == "Analytics Dashboard"
    assert "React" in projs[1]["description"]
    assert "React" in projs[1]["technologies"] or "Tailwind" in projs[1]["technologies"]


def test_skill_categorization_hardening():
    """Verify canonical category assignment according to system taxonomy (e.g. REST APIs is 'other')."""
    from backend.app.services.rule_extractor import categorize_skill

    assert categorize_skill("Python") == "programming_language"
    assert categorize_skill("JavaScript") == "programming_language"
    assert categorize_skill("FastAPI") == "framework"
    assert categorize_skill("React") == "framework"
    assert categorize_skill("PostgreSQL") == "database"
    assert categorize_skill("MongoDB") == "database"
    assert categorize_skill("Docker") == "devops"
    assert categorize_skill("NumPy") == "library"
    assert categorize_skill("Pandas") == "library"
    assert categorize_skill("REST APIs") == "other"
    assert categorize_skill("Microservices") == "other"


def test_reconcile_candidate_profile_recovers_merged_job():
    """Verify that post-reconciliation unmerges jobs, cleans education and projects, and standardizes skills."""
    from backend.app.services.resume_extractor import reconcile_candidate_profile
    from backend.app.schemas import (
        PersonalInfo,
        ExperienceItem,
        EducationItem,
        ProjectItem,
        SkillItem,
    )

    raw_text = (
        "Alice Smith\n"
        "alice@example.com\n\n"
        "Work Experience\n"
        "Senior Software Engineer - CloudCorp (2022 - Present)\n"
        "- Led engineering team\n"
        "Software Developer - AppLabs (2019 - 2022)\n"
        "- Developed backend services\n\n"
        "Education\n"
        "B.Tech in Computer Science - State Tech University (2015 - 2019)\n\n"
        "Projects\n"
        "E-Commerce Microservices: Built an API gateway using FastAPI\n\n"
        "Skills\n"
        "Python, REST APIs, PostgreSQL\n"
    )

    # Simulated flawed LLM output (merged experience, degree in institution, long project name, misclassified skill)
    flawed_profile = CandidateProfile(
        personal_info=PersonalInfo(name="Alice Smith", email="alice@example.com"),
        skills=[
            SkillItem(name="Python", category="tool"),
            SkillItem(name="REST APIs", category="framework"),
            SkillItem(name="PostgreSQL", category="database"),
        ],
        experience=[
            ExperienceItem(
                title="Senior Software Engineer",
                company="- CloudCorp / AppLabs",
                start_date="2022",
                end_date="2019",
                is_current=True,
                description="Led engineering team and developed backend services",
            )
        ],
        education=[
            EducationItem(
                institution="B.Tech in Computer Science, State Tech University (2015 - 2019)",
                field=None,
                start_year=2019,
                end_year=2015,
            )
        ],
        projects=[
            ProjectItem(
                name="E-Commerce Microservices: Built an API gateway using FastAPI",
                description=None,
            )
        ],
    )

    from backend.app.services.rule_extractor import extract_sections
    sections = extract_sections(raw_text)

    reconciled = reconcile_candidate_profile(flawed_profile, raw_text, sections)

    # Experience must be unpacked into 2 distinct jobs
    assert len(reconciled.experience) == 2
    assert reconciled.experience[0].title == "Senior Software Engineer"
    assert reconciled.experience[0].company == "CloudCorp"
    assert reconciled.experience[1].title == "Software Developer"
    assert reconciled.experience[1].company == "AppLabs"

    # Education must have degree, field, clean institution, and corrected years
    assert len(reconciled.education) == 1
    edu = reconciled.education[0]
    assert edu.degree == "B.Tech"
    assert edu.field == "Computer Science"
    assert "B.Tech" not in edu.institution
    assert edu.start_year == 2015
    assert edu.end_year == 2019

    # Project name and description must be split
    assert reconciled.projects[0].name == "E-Commerce Microservices"
    assert "FastAPI" in reconciled.projects[0].description

    # Skills must be standardized
    skill_map = {s.name: s.category for s in reconciled.skills}
    assert skill_map["Python"] == "programming_language"
    assert skill_map["REST APIs"] == "other"
    assert skill_map["PostgreSQL"] == "database"


def test_all_four_synthetic_resumes_extract_e2e(client):
    """Verify that all 4 synthetic resumes extract cleanly via the API."""
    resumes = [
        ("synthetic_software_engineer.pdf", "application/pdf", 2, 1),
        ("synthetic_data_scientist.pdf", "application/pdf", 1, 2),
        ("synthetic_frontend_developer.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 1, 1),
        ("synthetic_junior_intern.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 0, 1),
    ]

    for filename, mime, expected_min_exp, expected_min_edu in resumes:
        file_path = SAMPLE_DIR / filename
        assert file_path.exists()
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        response = client.post(
            "/api/v1/resumes/extract",
            files={"file": (filename, file_bytes, mime)},
        )
        assert response.status_code == 200, f"Failed for {filename}: {response.text}"
        data = response.json()
        profile = data["profile"]

        assert profile["personal_info"]["name"] is not None
        assert profile["personal_info"]["email"] is not None
        assert len(profile["skills"]) > 0
        assert len(profile["experience"]) >= expected_min_exp
        assert len(profile["education"]) >= expected_min_edu

        # Verify no bullet leaks in companies
        for exp in profile["experience"]:
            if exp["company"]:
                assert not exp["company"].startswith(("-", "*", "•"))

        # Verify no degree leaks in institutions
        for edu in profile["education"]:
            if edu["institution"] and edu["degree"]:
                assert edu["degree"] not in edu["institution"]

