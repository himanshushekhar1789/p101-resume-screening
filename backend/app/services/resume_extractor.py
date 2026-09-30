import logging
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
from backend.app.schemas import (
    CandidateProfile,
    SkillItem,
    ExperienceItem,
    EducationItem,
    ProjectItem,
    VALID_SKILL_CATEGORIES,
)
from backend.app.ai.llm_client import BaseLLMClient, get_llm_client
from backend.app.ai.validators import validate_llm_json, LLMValidationError
from backend.app.services.rule_extractor import (
    extract_email,
    extract_phone,
    extract_links,
    extract_sections,
    categorize_skill,
    parse_experience_blocks,
    parse_education_blocks,
    parse_project_blocks,
)

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).parent.parent / "ai" / "prompts" / "resume_extraction.txt"


def load_prompt_template() -> str:
    """Load the centralized prompt template for resume extraction."""
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Resume extraction prompt template not found at {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding="utf-8")


def reconcile_candidate_profile(
    profile: CandidateProfile,
    raw_text: str,
    sections: Dict[str, str],
) -> CandidateProfile:
    """
    Reconcile and harden LLM output against deterministic rule-based extractions.
    Prevents merged experiences, cleans company/institution leaks, fixes inverted dates,
    separates project names from descriptions, and enforces canonical skill categories.
    """
    # 1. Contact & Identity reconciliation
    rule_email = extract_email(raw_text)
    rule_phone = extract_phone(raw_text)
    rule_links = extract_links(raw_text)

    if not profile.personal_info.email and rule_email:
        profile.personal_info.email = rule_email

    if not profile.personal_info.phone and rule_phone:
        profile.personal_info.phone = rule_phone

    if not profile.personal_info.linkedin_url and rule_links.get("linkedin_url"):
        profile.personal_info.linkedin_url = rule_links["linkedin_url"]

    if not profile.personal_info.github_url and rule_links.get("github_url"):
        profile.personal_info.github_url = rule_links["github_url"]

    if not profile.personal_info.name:
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        if lines:
            first_line = lines[0]
            if len(first_line.split()) <= 4 and not any(c in first_line for c in "@/:"):
                profile.personal_info.name = first_line

    # Determine section texts (only fall back to raw_text if resume has no section headers)
    has_headers = len(sections) > 1 and "content" not in sections
    exp_text = sections.get("experience", "" if has_headers else raw_text)
    edu_text = sections.get("education", "" if has_headers else raw_text)
    proj_text = sections.get("projects", "" if has_headers else raw_text)

    # 2. Experience reconciliation
    rule_experiences = parse_experience_blocks(exp_text)
    if not profile.experience and rule_experiences:
        profile.experience = [ExperienceItem(**item) for item in rule_experiences]
    elif len(profile.experience) == 1 and len(rule_experiences) >= 2:
        # Detected multiple jobs erroneously merged into one by LLM
        profile.experience = [ExperienceItem(**item) for item in rule_experiences]
    else:
        for exp in profile.experience:
            if exp.company:
                exp.company = exp.company.lstrip("-*• \t").strip()
                if exp.company.startswith(("-", "*", "•", "–")) or len(exp.company) > 80:
                    exp.company = None
            if not exp.company and rule_experiences:
                for re_item in rule_experiences:
                    if exp.title and re_item.get("title") and exp.title.lower() in re_item["title"].lower():
                        exp.company = re_item.get("company")
                        break
            if exp.start_date and exp.end_date:
                s_year_m = re.search(r"\b(19\d\d|20\d\d)\b", exp.start_date)
                e_year_m = re.search(r"\b(19\d\d|20\d\d)\b", exp.end_date)
                if s_year_m and e_year_m:
                    s_yr, e_yr = int(s_year_m.group(1)), int(e_year_m.group(1))
                    if e_yr < s_yr:
                        exp.start_date, exp.end_date = exp.end_date, exp.start_date
            if exp.is_current and exp.end_date and exp.end_date.lower() not in ["present", "current", "now"]:
                exp.end_date = None

    # 3. Education reconciliation
    rule_education = parse_education_blocks(edu_text)
    if not profile.education and rule_education:
        profile.education = [EducationItem(**item) for item in rule_education]
    else:
        for edu in profile.education:
            if edu.institution:
                edu.institution = re.sub(r"\s*\(\s*\d{4}.*?\)", "", edu.institution).strip(" -—,")
                # Extract degree if leaked into institution
                deg_m = re.search(
                    r"(B\.?Tech(?:nology)?|Bachelor(?:\s+of\s+[A-Za-z]+)?|B\.?S\.|B\.?S\b|B\.?A\.|B\.?A\b|M\.?Tech|Master(?:\s+of\s+[A-Za-z]+)?|M\.?S\.|M\.?S\b|Ph\.?D\.|Ph\.?D\b|Diploma\b)",
                    edu.institution,
                    re.I,
                )
                if deg_m:
                    if not edu.degree:
                        edu.degree = deg_m.group(0).strip()
                    edu.institution = re.sub(re.escape(deg_m.group(0)), "", edu.institution, flags=re.I).strip(" -—,")
                # Extract field if leaked into institution
                field_leak_m = re.search(r"\bin\s+([^—\n,-]+?)(?=\s*[-–—,]|\s+(?:from|at)\s+|$)", edu.institution, re.I)
                if field_leak_m:
                    f_cand = field_leak_m.group(1).strip()
                    if not any(k in f_cand.lower() for k in ["university", "college", "institute", "school"]):
                        if not edu.field:
                            edu.field = f_cand
                        edu.institution = re.sub(r"\bin\s+" + re.escape(f_cand), "", edu.institution, flags=re.I).strip(" -—,")
            if not edu.field and rule_education:
                for r_edu in rule_education:
                    if r_edu.get("field"):
                        edu.field = r_edu["field"]
                        break
            if edu.start_year and edu.end_year and edu.end_year < edu.start_year:
                edu.start_year, edu.end_year = edu.end_year, edu.start_year

    # 4. Project reconciliation
    rule_projects = parse_project_blocks(proj_text)
    if not profile.projects and rule_projects:
        profile.projects = [ProjectItem(**item) for item in rule_projects]
    else:
        for proj in profile.projects:
            proj.name = proj.name.lstrip("-*• \t").strip()
            colon_split = re.split(r":\s+", proj.name, maxsplit=1)
            dash_split = re.split(r"\s+[-–—]\s+", proj.name, maxsplit=1)
            if len(colon_split) == 2 and not proj.name.lower().startswith(("technologies", "tools", "tech stack")):
                title, desc = colon_split[0].strip(), colon_split[1].strip()
                proj.name = title
                if not proj.description:
                    proj.description = desc
                else:
                    proj.description = f"{desc} {proj.description}".strip()
            elif len(dash_split) == 2 and (len(dash_split[1].split()) > 3 or len(proj.name.split()) > 6):
                title, desc = dash_split[0].strip(), dash_split[1].strip()
                proj.name = title
                if not proj.description:
                    proj.description = desc
                else:
                    proj.description = f"{desc} {proj.description}".strip()

    # 5. Skill categorization reconciliation
    seen_skills = set()
    cleaned_skills: List[SkillItem] = []
    for s in profile.skills:
        s_name = s.name.lstrip("-*• \t").strip()
        if not s_name:
            continue
        norm_key = s_name.lower()
        if norm_key in seen_skills:
            continue
        seen_skills.add(norm_key)

        cat = categorize_skill(s_name)
        if cat != "other":
            s.category = cat
        elif norm_key in ["rest apis", "rest api", "rest", "restful api", "restful apis"]:
            s.category = "other"
        elif s.category not in VALID_SKILL_CATEGORIES:
            s.category = "other"

        s.name = s_name
        cleaned_skills.append(s)

    profile.skills = cleaned_skills
    return profile


async def extract_candidate_profile(
    raw_text: str,
    llm_client: Optional[BaseLLMClient] = None,
) -> CandidateProfile:
    """
    Extract a validated structured candidate profile from raw resume text.
    Combines rule-based extraction with LLM reasoning, Pydantic validation, and post-reconciliation.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Cannot extract profile from empty resume text.")

    client = llm_client or get_llm_client()

    # Step 1: Deterministic rule-based extraction
    sections = extract_sections(raw_text)

    # Step 2: Prepare versioned LLM prompt
    template = load_prompt_template()
    prompt = template.replace("{resume_text}", raw_text)

    # Step 3: Call LLM client
    try:
        raw_llm_response = await client.generate(prompt, temperature=0.1)
    except Exception as e:
        logger.error(f"Error during LLM profile generation: {str(e)}")
        raise

    # Step 4: Validate and parse JSON with Pydantic
    try:
        profile = validate_llm_json(raw_llm_response, CandidateProfile)
    except LLMValidationError as e:
        logger.warning(f"Initial LLM validation failed: {str(e)}. Attempting safe recovery.")
        raise

    # Step 5: Ground-truth reconciliation and quality hardening
    profile = reconcile_candidate_profile(profile, raw_text, sections)

    return profile
