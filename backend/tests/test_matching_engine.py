"""
Comprehensive Test Suite for Phase 6: Candidate ↔ Job Requirement Matching Engine.

Validates:
1. Exact skill matching (canonical_exact).
2. Alias-normalized matching (alias_normalized).
3. Missing skill handling (unmatched).
4. Version compatibility matching (version_compatible).
5. Similar-looking but distinct skills (Java != JavaScript, C != C++, etc.).
6. Must-have and nice-to-have priority preservation.
7. General experience matching (experience_verified vs experience_insufficient).
8. Skill-specific experience matching (experience_verified vs not_evaluable).
9. Education degree and field matching (full match vs partial match).
10. Certification matching.
11. Evidence traceability and synthesis.
12. Absence of scoring / percentages / ranking.
13. The 5 required synthetic scenarios in Section 27.
14. REST API endpoint /api/v1/matching/analyze.
15. E2E pipeline matching using real synthetic resumes and JDs.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas import (
    CandidateProfile,
    JobProfile,
    SkillItem,
    JobSkillRequirement,
    JobExperienceRequirement,
    JobEducationRequirement,
    JobCertificationRequirement,
    ExperienceItem,
    EducationItem,
    CertificationItem,
    MatchStatus,
    MatchMethod,
)
from backend.app.services.matching_engine import MatchingEngine
from backend.app.services.skill_normalizer import (
    normalize_candidate_skills,
    normalize_job_skills,
)
from backend.app.services.document_parser import parse_document
from backend.app.services.resume_extractor import extract_candidate_profile
from backend.app.services.jd_analyzer import analyze_job_description

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Skill Matching Tests
# ---------------------------------------------------------------------------
def test_exact_skill_match():
    cand = CandidateProfile(
        skills=[SkillItem(name="Python", category="programming_language")]
    )
    cand.normalized_skills = normalize_candidate_skills(cand.skills)

    job = JobProfile(
        skills=[JobSkillRequirement(name="Python", category="programming_language", priority="must_have")]
    )
    job.normalized_skills = normalize_job_skills(job.skills)

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    assert len(res.matches) == 1
    m = res.matches[0]
    assert m.requirement.name == "Python"
    assert m.status == MatchStatus.MATCHED
    assert m.match_method == MatchMethod.CANONICAL_EXACT
    assert m.requirement.priority == "must_have"
    assert any("Python" in ev for ev in m.candidate_evidence)


def test_alias_normalized_skill_match():
    cand = CandidateProfile(
        skills=[SkillItem(name="JS", category="programming_language")]
    )
    cand.normalized_skills = normalize_candidate_skills(cand.skills)

    job = JobProfile(
        skills=[JobSkillRequirement(name="JavaScript", category="programming_language", priority="must_have")]
    )
    job.normalized_skills = normalize_job_skills(job.skills)

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    assert len(res.matches) == 1
    m = res.matches[0]
    assert m.requirement.name == "JavaScript"
    assert m.status == MatchStatus.MATCHED
    assert m.match_method == MatchMethod.ALIAS_NORMALIZED
    # Preserves original alias 'JS' in evidence
    assert any("JS" in ev for ev in m.candidate_evidence)


def test_version_compatible_skill_match():
    cand = CandidateProfile(
        skills=[SkillItem(name="Python 3.11", category="programming_language")]
    )
    cand.normalized_skills = normalize_candidate_skills(cand.skills)

    job = JobProfile(
        skills=[JobSkillRequirement(name="Python", category="programming_language", priority="must_have")]
    )
    job.normalized_skills = normalize_job_skills(job.skills)

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    assert len(res.matches) == 1
    m = res.matches[0]
    assert m.requirement.name == "Python"
    assert m.status == MatchStatus.MATCHED
    assert m.match_method == MatchMethod.VERSION_COMPATIBLE


def test_missing_skill_unmatched():
    cand = CandidateProfile(
        skills=[SkillItem(name="Python", category="programming_language")]
    )
    cand.normalized_skills = normalize_candidate_skills(cand.skills)

    job = JobProfile(
        skills=[JobSkillRequirement(name="PostgreSQL", category="database", priority="must_have")]
    )
    job.normalized_skills = normalize_job_skills(job.skills)

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    assert len(res.matches) == 1
    m = res.matches[0]
    assert m.requirement.name == "PostgreSQL"
    assert m.status == MatchStatus.UNMATCHED
    assert m.match_method == MatchMethod.UNMATCHED
    assert len(m.candidate_evidence) == 0


def test_distinct_skills_not_confused():
    # Java != JavaScript
    cand_java = CandidateProfile(skills=[SkillItem(name="Java")])
    cand_java.normalized_skills = normalize_candidate_skills(cand_java.skills)
    job_js = JobProfile(skills=[JobSkillRequirement(name="JavaScript")])
    job_js.normalized_skills = normalize_job_skills(job_js.skills)

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand_java, job_js)
    assert res.matches[0].status == MatchStatus.UNMATCHED

    # C != C++ and C != C#
    cand_c = CandidateProfile(skills=[SkillItem(name="C")])
    cand_c.normalized_skills = normalize_candidate_skills(cand_c.skills)

    job_cpp = JobProfile(skills=[JobSkillRequirement(name="C++")])
    job_cpp.normalized_skills = normalize_job_skills(job_cpp.skills)

    job_csharp = JobProfile(skills=[JobSkillRequirement(name="C#")])
    job_csharp.normalized_skills = normalize_job_skills(job_csharp.skills)

    assert engine.match_candidate_to_job(cand_c, job_cpp).matches[0].status == MatchStatus.UNMATCHED
    assert engine.match_candidate_to_job(cand_c, job_csharp).matches[0].status == MatchStatus.UNMATCHED


def test_priority_preservation():
    cand = CandidateProfile(
        skills=[
            SkillItem(name="Python"),
            SkillItem(name="AWS"),
        ]
    )
    cand.normalized_skills = normalize_candidate_skills(cand.skills)

    job = JobProfile(
        skills=[
            JobSkillRequirement(name="Python", priority="must_have"),
            JobSkillRequirement(name="AWS", priority="nice_to_have"),
        ]
    )
    job.normalized_skills = normalize_job_skills(job.skills)

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    matches_by_name = {m.requirement.name: m for m in res.matches}
    assert matches_by_name["Python"].requirement.priority == "must_have"
    assert matches_by_name["AWS"].requirement.priority == "nice_to_have"
    assert res.summary.must_have_matched == 1
    assert res.summary.nice_to_have_matched == 1


# ---------------------------------------------------------------------------
# 2. Experience Matching Tests
# ---------------------------------------------------------------------------
def test_general_experience_satisfied():
    cand = CandidateProfile(
        experience=[
            ExperienceItem(
                title="Software Engineer",
                company="Alpha Corp",
                start_date="2019",
                end_date="2022",
            ),
            ExperienceItem(
                title="Senior Backend Engineer",
                company="Beta Corp",
                start_date="2022",
                end_date="2024",
            ),
        ]
    )
    job = JobProfile(
        experience_requirements=[
            JobExperienceRequirement(
                text="3+ years of backend engineering",
                minimum_years=3.0,
                priority="must_have",
            )
        ]
    )

    engine = MatchingEngine(current_year=2026.0)
    res = engine.match_candidate_to_job(cand, job)

    m = res.matches[0]
    assert m.status == MatchStatus.MATCHED
    assert m.match_method == MatchMethod.EXPERIENCE_VERIFIED
    assert len(m.candidate_evidence) >= 2


def test_general_experience_insufficient():
    cand = CandidateProfile(
        experience=[
            ExperienceItem(
                title="Junior Developer",
                company="Startup Inc",
                start_date="2022",
                end_date="2024",
            )
        ]
    )
    job = JobProfile(
        experience_requirements=[
            JobExperienceRequirement(
                text="5+ years of software development experience",
                minimum_years=5.0,
                priority="must_have",
            )
        ]
    )

    engine = MatchingEngine(current_year=2026.0)
    res = engine.match_candidate_to_job(cand, job)

    m = res.matches[0]
    assert m.status == MatchStatus.UNMATCHED
    assert m.match_method == MatchMethod.EXPERIENCE_INSUFFICIENT


def test_skill_specific_experience_not_evaluable_when_tenure_undated():
    # Candidate lists Python as skill, but role does NOT mention Python or specific Python tenure
    cand = CandidateProfile(
        skills=[SkillItem(name="Python")],
        experience=[
            ExperienceItem(
                title="Software Engineer",
                company="TechCorp",
                start_date="2020",
                end_date="2024",
                description="Built enterprise services and worked on web platforms.",
                skills=["Java", "C++"],  # No Python mentioned here
            )
        ],
    )
    cand.normalized_skills = normalize_candidate_skills(cand.skills)

    job = JobProfile(
        skills=[
            JobSkillRequirement(
                name="Python",
                minimum_years=3.0,
                priority="must_have",
                evidence="3+ years of Python experience required",
            )
        ]
    )
    job.normalized_skills = normalize_job_skills(job.skills)

    engine = MatchingEngine(current_year=2026.0)
    res = engine.match_candidate_to_job(cand, job)

    m = res.matches[0]
    # As instructed in Section 13 & 28: do NOT claim 4 years Python. Must be not_evaluable!
    assert m.status == MatchStatus.NOT_EVALUABLE
    assert m.match_method == MatchMethod.NOT_EVALUABLE
    assert "tenure cannot be verified" in m.reason.lower()


# ---------------------------------------------------------------------------
# 3. Education Matching Tests
# ---------------------------------------------------------------------------
def test_education_full_match():
    cand = CandidateProfile(
        education=[
            EducationItem(
                degree="B.Tech",
                field="Computer Science",
                institution="State Tech University",
            )
        ]
    )
    job = JobProfile(
        education_requirements=[
            JobEducationRequirement(
                degree="Bachelor's",
                field="Computer Science",
                priority="must_have",
            )
        ]
    )

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    m = res.matches[0]
    assert m.status == MatchStatus.MATCHED
    assert m.match_method == MatchMethod.EDUCATION_MATCH
    assert "B.Tech" in m.candidate_evidence[0]


def test_education_partial_match_degree_matches_field_differs():
    # Section 16 & Scenario 5
    cand = CandidateProfile(
        education=[
            EducationItem(
                degree="B.Tech",
                field="Mechanical Engineering",
                institution="State Tech University",
            )
        ]
    )
    job = JobProfile(
        education_requirements=[
            JobEducationRequirement(
                degree="Bachelor's",
                field="Computer Science",
                priority="must_have",
            )
        ]
    )

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    m = res.matches[0]
    assert m.status == MatchStatus.PARTIAL
    assert m.match_method == MatchMethod.EDUCATION_PARTIAL
    assert "does not match" in m.reason.lower()


# ---------------------------------------------------------------------------
# 4. Certification Matching Tests
# ---------------------------------------------------------------------------
def test_certification_matched_and_missing():
    cand = CandidateProfile(
        certifications=[
            CertificationItem(
                name="AWS Certified Solutions Architect",
                issuing_organization="Amazon Web Services",
            )
        ]
    )
    job = JobProfile(
        certification_requirements=[
            JobCertificationRequirement(
                name="AWS Certified Solutions Architect",
                priority="nice_to_have",
            ),
            JobCertificationRequirement(
                name="CKA (Certified Kubernetes Administrator)",
                priority="nice_to_have",
            ),
        ]
    )

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    assert len(res.matches) == 2
    aws_m = next(m for m in res.matches if "AWS" in m.requirement.name)
    cka_m = next(m for m in res.matches if "CKA" in m.requirement.name)

    assert aws_m.status == MatchStatus.MATCHED
    assert aws_m.match_method == MatchMethod.CERTIFICATION_MATCH
    assert aws_m.requirement.priority == "nice_to_have"

    assert cka_m.status == MatchStatus.UNMATCHED
    assert cka_m.match_method == MatchMethod.UNMATCHED


# ---------------------------------------------------------------------------
# 5. The 5 Specific Synthetic Scenarios (Section 27)
# ---------------------------------------------------------------------------
def test_scenario_1_strong_skill_match():
    """
    Scenario 1:
    Candidate: Python, FastAPI, PostgreSQL, Docker, AWS
    JD: Python (must), FastAPI (must), PostgreSQL (must), AWS (nice)
    Expected: All 4 matched
    """
    cand = CandidateProfile(
        skills=[
            SkillItem(name="Python"),
            SkillItem(name="FastAPI"),
            SkillItem(name="PostgreSQL"),
            SkillItem(name="Docker"),
            SkillItem(name="AWS"),
        ]
    )
    cand.normalized_skills = normalize_candidate_skills(cand.skills)

    job = JobProfile(
        skills=[
            JobSkillRequirement(name="Python", priority="must_have"),
            JobSkillRequirement(name="FastAPI", priority="must_have"),
            JobSkillRequirement(name="PostgreSQL", priority="must_have"),
            JobSkillRequirement(name="AWS", priority="nice_to_have"),
        ]
    )
    job.normalized_skills = normalize_job_skills(job.skills)

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    assert res.summary.total_requirements == 4
    assert res.summary.matched == 4
    assert res.summary.unmatched == 0
    assert res.summary.partial == 0


def test_scenario_2_missing_required_skill():
    """
    Scenario 2:
    Candidate: Python, FastAPI, MySQL
    JD: Python (must), FastAPI (must), PostgreSQL (must)
    Expected: Python -> matched, FastAPI -> matched, PostgreSQL -> unmatched
    """
    cand = CandidateProfile(
        skills=[
            SkillItem(name="Python"),
            SkillItem(name="FastAPI"),
            SkillItem(name="MySQL"),
        ]
    )
    cand.normalized_skills = normalize_candidate_skills(cand.skills)

    job = JobProfile(
        skills=[
            JobSkillRequirement(name="Python", priority="must_have"),
            JobSkillRequirement(name="FastAPI", priority="must_have"),
            JobSkillRequirement(name="PostgreSQL", priority="must_have"),
        ]
    )
    job.normalized_skills = normalize_job_skills(job.skills)

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    matches_map = {m.requirement.name: m for m in res.matches}
    assert matches_map["Python"].status == MatchStatus.MATCHED
    assert matches_map["FastAPI"].status == MatchStatus.MATCHED
    assert matches_map["PostgreSQL"].status == MatchStatus.UNMATCHED
    assert res.summary.matched == 2
    assert res.summary.unmatched == 1


def test_scenario_3_experience_issue():
    """
    Scenario 3:
    JD: 5+ years backend software engineering
    Candidate: 2 years explicit backend experience
    Expected: unmatched (experience_insufficient)
    """
    cand = CandidateProfile(
        experience=[
            ExperienceItem(
                title="Backend Developer",
                company="TechStartup",
                start_date="2022",
                end_date="2024",
            )
        ]
    )
    job = JobProfile(
        experience_requirements=[
            JobExperienceRequirement(
                text="5+ years backend software engineering",
                minimum_years=5.0,
                priority="must_have",
            )
        ]
    )

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    assert res.matches[0].status == MatchStatus.UNMATCHED
    assert res.matches[0].match_method == MatchMethod.EXPERIENCE_INSUFFICIENT


def test_scenario_4_insufficient_evidence():
    """
    Scenario 4:
    JD: 3+ years Python
    Candidate: Python listed as a skill, 2 years Software Developer experience (no explicit Python duration)
    Expected: not_evaluable (Do NOT assume 2 years Python)
    """
    cand = CandidateProfile(
        skills=[SkillItem(name="Python")],
        experience=[
            ExperienceItem(
                title="Software Developer",
                company="GeneralCo",
                start_date="2022",
                end_date="2024",
                description="General full-stack development with Java and JavaScript.",
            )
        ],
    )
    cand.normalized_skills = normalize_candidate_skills(cand.skills)

    job = JobProfile(
        experience_requirements=[
            JobExperienceRequirement(
                text="3+ years of Python experience",
                skill="Python",
                minimum_years=3.0,
                priority="must_have",
            )
        ]
    )

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    assert res.matches[0].status == MatchStatus.NOT_EVALUABLE
    assert res.matches[0].match_method == MatchMethod.NOT_EVALUABLE


def test_scenario_5_education_partial():
    """
    Scenario 5:
    JD: Bachelor's degree in Computer Science
    Candidate: B.Tech in Mechanical Engineering
    Expected: partial (education_partial)
    """
    cand = CandidateProfile(
        education=[
            EducationItem(
                degree="B.Tech",
                field="Mechanical Engineering",
                institution="City College",
            )
        ]
    )
    job = JobProfile(
        education_requirements=[
            JobEducationRequirement(
                degree="Bachelor's degree",
                field="Computer Science",
                priority="must_have",
            )
        ]
    )

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)

    assert res.matches[0].status == MatchStatus.PARTIAL
    assert res.matches[0].match_method == MatchMethod.EDUCATION_PARTIAL


# ---------------------------------------------------------------------------
# 6. Absence of Score or Ranking Assertions
# ---------------------------------------------------------------------------
def test_no_score_or_percentage_in_output():
    cand = CandidateProfile(skills=[SkillItem(name="Python")])
    job = JobProfile(skills=[JobSkillRequirement(name="Python")])

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(cand, job)
    data = res.model_dump()

    # Assert that no scoring or ranking fields exist
    assert "score" not in data
    assert "total_score" not in data
    assert "match_percentage" not in data
    assert "ranking" not in data
    assert "score" not in data["summary"]
    assert "percentage" not in data["summary"]


# ---------------------------------------------------------------------------
# 7. REST API Integration Tests
# ---------------------------------------------------------------------------
def test_api_matching_analyze_endpoint():
    cand = CandidateProfile(
        skills=[
            SkillItem(name="Python"),
            SkillItem(name="FastAPI"),
        ],
        education=[
            EducationItem(degree="Bachelor of Science", field="Computer Science")
        ],
    )
    job = JobProfile(
        job_title="Backend Engineer",
        skills=[
            JobSkillRequirement(name="Python", priority="must_have"),
            JobSkillRequirement(name="Kubernetes", priority="nice_to_have"),
        ],
        education_requirements=[
            JobEducationRequirement(degree="Bachelor's", field="Computer Science")
        ],
    )

    payload = {
        "candidate": cand.model_dump(),
        "job": job.model_dump(),
        "candidate_id": "cand_123",
        "job_id": "job_456",
    }

    response = client.post("/api/v1/matching/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["candidate_id"] == "cand_123"
    assert data["job_id"] == "job_456"
    assert data["summary"]["total_requirements"] == 3
    assert data["summary"]["matched"] == 2
    assert data["summary"]["unmatched"] == 1


# ---------------------------------------------------------------------------
# 8. E2E Matching with Synthetic Files
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_e2e_synthetic_candidate_job_matching():
    with open("data/sample/resumes/synthetic_software_engineer.pdf", "rb") as fp:
        doc = parse_document(fp.read(), "synthetic_software_engineer.pdf")
    candidate = await extract_candidate_profile(doc.text)

    with open("data/sample/job_descriptions/backend_engineer_jd.txt", "r", encoding="utf-8") as fp:
        jd_text = fp.read()
    job = await analyze_job_description(jd_text)

    engine = MatchingEngine()
    res = engine.match_candidate_to_job(candidate, job)

    assert res.summary.total_requirements > 10
    assert res.summary.matched >= 8  # Strong backend match
    # Software engineer resume has Python, FastAPI, PostgreSQL, Docker, AWS, Degree in CS
    matched_names = {m.requirement.name for m in res.matches if m.status == MatchStatus.MATCHED}
    assert "Python" in matched_names
    assert "FastAPI" in matched_names
    assert "PostgreSQL" in matched_names
    assert "Docker" in matched_names


def test_api_matching_from_files_endpoint():
    with open("data/sample/resumes/synthetic_software_engineer.pdf", "rb") as rf:
        resume_bytes = rf.read()
    with open("data/sample/job_descriptions/backend_engineer_jd.pdf", "rb") as jf:
        job_bytes = jf.read()

    response = client.post(
        "/api/v1/matching/from-files",
        files={
            "resume_file": ("synthetic_software_engineer.pdf", resume_bytes, "application/pdf"),
            "job_file": ("backend_engineer_jd.pdf", job_bytes, "application/pdf"),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_requirements"] > 5
    assert data["summary"]["matched"] >= 5
    assert data["candidate_id"] == "synthetic_software_engineer.pdf"
    assert data["job_id"] == "backend_engineer_jd.pdf"

