import logging
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
from backend.app.schemas import (
    JobProfile,
    JobSkillRequirement,
    JobExperienceRequirement,
    JobEducationRequirement,
    JobCertificationRequirement,
    JobOtherRequirement,
    JobRequirementItem,
    VALID_SKILL_CATEGORIES,
)
from backend.app.ai.llm_client import BaseLLMClient, get_llm_client
from backend.app.ai.validators import validate_llm_json, LLMValidationError
from backend.app.services.rule_extractor import categorize_skill
from backend.app.services.jd_rule_extractor import (
    extract_jd_sections,
    detect_priority,
    parse_job_profile_rules,
)

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).parent.parent / "ai" / "prompts" / "job_extraction.txt"


def load_jd_prompt_template() -> str:
    """Load the centralized prompt template for job description analysis."""
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Job extraction prompt template not found at {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding="utf-8")


def reconcile_job_profile(
    profile: JobProfile,
    raw_text: str,
    sections: Dict[str, str],
    rule_data: Dict[str, Any],
    initial_title: Optional[str] = None,
) -> JobProfile:
    """
    Reconcile and harden LLM-extracted JobProfile against deterministic rules.
    Guarantees:
    1. Title / Company / Location consistency.
    2. Strict must-have vs nice-to-have classification (enforcing 'is a plus' as nice_to_have).
    3. Category normalization according to canonical skill taxonomy.
    4. Responsibilities strictly isolated from qualifications.
    5. No invented requirements (e.g. empty degree remains empty if not mentioned).
    6. Synchronized must_have and nice_to_have collections.
    """
    # 1. Metadata Reconciliation
    if initial_title:
        profile.job_title = initial_title
    elif not profile.job_title and rule_data.get("job_title"):
        profile.job_title = rule_data["job_title"]

    if not profile.company and rule_data.get("company"):
        profile.company = rule_data["company"]

    if not profile.location and rule_data.get("location"):
        profile.location = rule_data["location"]

    if not profile.summary and rule_data.get("summary"):
        profile.summary = rule_data["summary"]

    # 2. Skill Requirements Reconciliation
    if not profile.skills and rule_data.get("skills"):
        profile.skills = [JobSkillRequirement(**s) for s in rule_data["skills"]]
    else:
        seen_skills = set()
        cleaned_skills: List[JobSkillRequirement] = []
        for s in profile.skills:
            clean_name = s.name.strip().lstrip("-*• ")
            if not clean_name:
                continue
            norm_key = clean_name.lower()
            if norm_key in seen_skills:
                continue
            seen_skills.add(norm_key)

            s.name = clean_name
            # Re-evaluate category
            cat = categorize_skill(clean_name)
            if cat != "other":
                s.category = cat
            elif norm_key in ["rest apis", "rest api", "rest", "microservices"]:
                s.category = "other"
            elif s.category not in VALID_SKILL_CATEGORIES:
                s.category = "other"

            # Check explicit phrasing in evidence
            if s.evidence:
                s.priority = detect_priority(s.evidence, default_priority=s.priority)

            cleaned_skills.append(s)
        profile.skills = cleaned_skills

    # 3. Experience Requirements Reconciliation
    if not profile.experience_requirements and rule_data.get("experience_requirements"):
        profile.experience_requirements = [
            JobExperienceRequirement(**e) for e in rule_data["experience_requirements"]
        ]
    else:
        for exp in profile.experience_requirements:
            exp.text = exp.text.strip().lstrip("-*• ")
            if exp.evidence:
                exp.priority = detect_priority(exp.evidence, default_priority=exp.priority)

    # 4. Education Requirements Reconciliation
    if not profile.education_requirements and rule_data.get("education_requirements"):
        profile.education_requirements = [
            JobEducationRequirement(**ed) for ed in rule_data["education_requirements"]
        ]
    else:
        for edu in profile.education_requirements:
            if edu.evidence:
                edu.priority = detect_priority(edu.evidence, default_priority=edu.priority)

    # 5. Certification Requirements Reconciliation
    if not profile.certification_requirements and rule_data.get("certification_requirements"):
        profile.certification_requirements = [
            JobCertificationRequirement(**c) for c in rule_data["certification_requirements"]
        ]
    else:
        for cert in profile.certification_requirements:
            cert.name = cert.name.strip().lstrip("-*• ")
            if cert.evidence:
                cert.priority = detect_priority(cert.evidence, default_priority=cert.priority)

    # 6. Other Requirements Reconciliation
    if not profile.other_requirements and rule_data.get("other_requirements"):
        profile.other_requirements = [
            JobOtherRequirement(**o) for o in rule_data["other_requirements"]
        ]

    # 7. Responsibilities Reconciliation (Guaranteed isolated from qualifications)
    if not profile.responsibilities and rule_data.get("responsibilities"):
        profile.responsibilities = rule_data["responsibilities"]
    else:
        cleaned_resp = []
        for r in profile.responsibilities:
            c = r.strip().lstrip("-*• ")
            c = re.sub(r"^\d+\.\s*", "", c).strip()
            if c:
                cleaned_resp.append(c)
        profile.responsibilities = cleaned_resp

    # 8. Synchronize must_have and nice_to_have Collections
    must_have: List[JobRequirementItem] = []
    nice_to_have: List[JobRequirementItem] = []

    # From skills
    for s in profile.skills:
        req_item = JobRequirementItem(
            text=s.evidence or f"Proficiency in {s.name}",
            type="skill",
            priority=s.priority,
            skill=s.name,
            minimum_years=s.minimum_years,
            evidence=s.evidence,
        )
        if s.priority == "must_have":
            must_have.append(req_item)
        else:
            nice_to_have.append(req_item)

    # From experience
    for exp in profile.experience_requirements:
        req_item = JobRequirementItem(
            text=exp.text,
            type="experience",
            priority=exp.priority,
            skill=exp.skill,
            minimum_years=exp.minimum_years,
            evidence=exp.evidence,
        )
        if exp.priority == "must_have":
            must_have.append(req_item)
        else:
            nice_to_have.append(req_item)

    # From education
    for edu in profile.education_requirements:
        deg_text = edu.degree or "Degree"
        fld_text = f" in {edu.field}" if edu.field else ""
        req_item = JobRequirementItem(
            text=edu.evidence or f"{deg_text}{fld_text}",
            type="education",
            priority=edu.priority,
            skill=None,
            minimum_years=None,
            evidence=edu.evidence,
        )
        if edu.priority == "must_have":
            must_have.append(req_item)
        else:
            nice_to_have.append(req_item)

    # From certifications
    for cert in profile.certification_requirements:
        req_item = JobRequirementItem(
            text=cert.evidence or cert.name,
            type="certification",
            priority=cert.priority,
            skill=None,
            minimum_years=None,
            evidence=cert.evidence,
        )
        if cert.priority == "must_have":
            must_have.append(req_item)
        else:
            nice_to_have.append(req_item)

    # From other
    for oth in profile.other_requirements:
        req_item = JobRequirementItem(
            text=oth.text,
            type=oth.type if oth.type in ["location", "language", "other"] else "other",
            priority=oth.priority,
            skill=None,
            minimum_years=None,
            evidence=oth.evidence,
        )
        if oth.priority == "must_have":
            must_have.append(req_item)
        else:
            nice_to_have.append(req_item)

    profile.must_have = must_have
    profile.nice_to_have = nice_to_have

    return profile


async def analyze_job_description(
    raw_text: str,
    initial_title: Optional[str] = None,
    llm_client: Optional[BaseLLMClient] = None,
) -> JobProfile:
    """
    Convert unstructured job description text into a structured, validated JobProfile.
    Combines rule-based extraction with LLM reasoning, Pydantic validation, and post-reconciliation.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Cannot analyze empty job description text.")

    client = llm_client or get_llm_client()

    # Step 1: Deterministic rule extraction
    sections = extract_jd_sections(raw_text)
    rule_data = parse_job_profile_rules(raw_text, initial_title)

    # Step 2: Prepare versioned LLM prompt
    template = load_jd_prompt_template()
    prompt = template.replace("{job_description}", raw_text)

    # Step 3: Call LLM client
    try:
        raw_llm_response = await client.generate(prompt, temperature=0.1)
    except Exception as e:
        logger.error(f"Error during LLM job description analysis: {str(e)}")
        raise

    # Step 4: Validate and parse JSON with Pydantic
    try:
        profile = validate_llm_json(raw_llm_response, JobProfile)
    except LLMValidationError as e:
        logger.warning(f"Initial LLM validation failed: {str(e)}. Falling back to deterministic profile.")
        profile = JobProfile(**rule_data)

    # Step 5: Ground-truth reconciliation and quality hardening
    profile = reconcile_job_profile(profile, raw_text, sections, rule_data, initial_title)

    return profile
