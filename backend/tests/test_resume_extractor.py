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
