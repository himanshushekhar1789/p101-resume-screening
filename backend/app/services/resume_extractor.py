import logging
from pathlib import Path
from typing import Optional
from backend.app.schemas import CandidateProfile
from backend.app.ai.llm_client import BaseLLMClient, get_llm_client
from backend.app.ai.validators import validate_llm_json, LLMValidationError
from backend.app.services.rule_extractor import (
    extract_email,
    extract_phone,
    extract_links,
    extract_sections,
)

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).parent.parent / "ai" / "prompts" / "resume_extraction.txt"


def load_prompt_template() -> str:
    """Load the centralized prompt template for resume extraction."""
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Resume extraction prompt template not found at {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding="utf-8")


async def extract_candidate_profile(
    raw_text: str,
    llm_client: Optional[BaseLLMClient] = None,
) -> CandidateProfile:
    """
    Extract a validated structured candidate profile from raw resume text.
    Combines rule-based extraction with LLM reasoning and Pydantic validation.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Cannot extract profile from empty resume text.")

    client = llm_client or get_llm_client()

    # Step 1: Deterministic rule-based extraction
    rule_email = extract_email(raw_text)
    rule_phone = extract_phone(raw_text)
    rule_links = extract_links(raw_text)
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

    # Step 5: Ground-truth reconciliation (rules override missing LLM extractions)
    if not profile.personal_info.email and rule_email:
        profile.personal_info.email = rule_email

    if not profile.personal_info.phone and rule_phone:
        profile.personal_info.phone = rule_phone

    if not profile.personal_info.linkedin_url and rule_links.get("linkedin_url"):
        profile.personal_info.linkedin_url = rule_links["linkedin_url"]

    if not profile.personal_info.github_url and rule_links.get("github_url"):
        profile.personal_info.github_url = rule_links["github_url"]

    # Fallback name from first line if still None
    if not profile.personal_info.name:
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        if lines:
            first_line = lines[0]
            if len(first_line.split()) <= 4 and not any(c in first_line for c in "@/:"):
                profile.personal_info.name = first_line

    return profile
