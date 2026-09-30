"""
Skill Normalization Service for P_101 Resume Screening System (Phase 5).

Transforms raw candidate and job description skills into machine-comparable,
canonical representations with strict taxonomy adherence, deduplication, and provenance tracking.

STRICT SCOPE:
- Deterministic only (0 LLM calls)
- Preserves original extracted strings
- Authoritative category assignment from taxonomy
- Conservative alias mapping and version stripping
- Protection against false positive generic words
- NO candidate-job matching, scoring, ranking, or similarity calculations.
"""

import re
import logging
from typing import List, Optional, Union, Dict, Any

from backend.app.schemas import (
    SkillItem,
    JobSkillRequirement,
    NormalizedSkill,
    NormalizedJobSkill,
    VALID_SKILL_CATEGORIES,
    RequirementPriority,
)
from backend.app.services.skill_taxonomy import (
    lookup_canonical_skill,
    FALSE_POSITIVE_WORDS,
)

logger = logging.getLogger(__name__)


def clean_skill_string(raw: str) -> str:
    """
    Clean whitespace and leading bullet/formatting tokens while preserving
    meaningful technical punctuation like C++, C#, .NET, Node.js, and CI/CD.
    """
    if not raw or not isinstance(raw, str):
        return ""

    # Strip leading bullets, numbers, hyphens, and whitespace
    cleaned = raw.strip()
    cleaned = re.sub(r"^[-*•–—~#\s]+", "", cleaned)
    cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
    cleaned = cleaned.strip(" \t\r\n,;")

    # Collapse multiple internal spaces to a single space
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def is_false_positive_skill(name: str) -> bool:
    """
    Check if a string represents an ordinary English/resume stopword
    rather than a real technical or professional skill.
    """
    if not name:
        return True

    lowered = name.strip().lower()

    # Reject purely numeric or single non-meaningful characters
    if lowered.isdigit() or len(lowered) < 1:
        return True

    # Single letter allowed only if it is "c" or "r" (known programming languages)
    if len(lowered) == 1 and lowered not in {"c", "r"}:
        return True

    if lowered in FALSE_POSITIVE_WORDS:
        return True

    return False


def normalize_skill(
    raw_name: str,
    hint_category: Optional[str] = None,
    source: str = "resume",
) -> Optional[NormalizedSkill]:
    """
    Normalize a single raw skill name string into a canonical NormalizedSkill.

    Returns None if the input is empty or recognized as a false positive.
    """
    cleaned = clean_skill_string(raw_name)
    if not cleaned or is_false_positive_skill(cleaned):
        return None

    # Step 1: Look up in centralized canonical registry
    lookup = lookup_canonical_skill(cleaned)

    if lookup is not None:
        canonical_name, category, method = lookup
        confidence = 1.0
    else:
        # Step 2: Unknown skill - preserve clean original text without hallucinating
        canonical_name = cleaned
        # Keep hint_category only if it's already a valid, non-'other' category
        if hint_category and hint_category.lower() in VALID_SKILL_CATEGORIES and hint_category.lower() != "other":
            category = hint_category.lower()
        else:
            category = "other"
        method = "unknown"
        confidence = 0.5

    return NormalizedSkill(
        canonical_name=canonical_name,
        original_name=raw_name.strip(),
        original_names=[raw_name.strip()],
        category=category,
        normalization_method=method,
        confidence=confidence,
        source=source,
    )


def normalize_candidate_skills(
    skills: List[Union[SkillItem, Dict[str, Any], str]],
    source: str = "resume",
) -> List[NormalizedSkill]:
    """
    Normalize and deduplicate candidate skills.

    If a candidate has 'Python', 'python', and 'Python 3', merges them into a single
    canonical 'Python' skill while preserving all original text variants in original_names.
    """
    dedup_map: Dict[str, NormalizedSkill] = {}

    for item in skills:
        raw_name = ""
        hint_cat = None

        if isinstance(item, SkillItem):
            raw_name = item.name
            hint_cat = item.category
        elif isinstance(item, dict):
            raw_name = item.get("name", "")
            hint_cat = item.get("category")
        elif isinstance(item, str):
            raw_name = item

        norm = normalize_skill(raw_name, hint_category=hint_cat, source=source)
        if norm is None:
            continue

        key = norm.canonical_name.lower()
        if key not in dedup_map:
            dedup_map[key] = norm
        else:
            existing = dedup_map[key]
            # Merge original_names without duplicates while preserving order
            for oname in norm.original_names:
                if oname not in existing.original_names:
                    existing.original_names.append(oname)
            # Retain higher confidence and more specific method
            if norm.confidence > existing.confidence:
                existing.confidence = norm.confidence
                existing.normalization_method = norm.normalization_method
            elif norm.confidence == existing.confidence and existing.normalization_method == "unknown":
                existing.normalization_method = norm.normalization_method
            # Category from registry takes precedence over "other"
            if existing.category == "other" and norm.category != "other":
                existing.category = norm.category

    return list(dedup_map.values())


def normalize_job_skills(
    skills: List[Union[JobSkillRequirement, Dict[str, Any], str]],
    source: str = "job_description",
) -> List[NormalizedJobSkill]:
    """
    Normalize and deduplicate job description skill requirements.

    Preserves priority, minimum_years, and evidence.
    If 'must_have' and 'nice_to_have' variants exist for the same canonical skill,
    'must_have' takes precedence. Takes max(minimum_years) and combines evidence.
    """
    dedup_map: Dict[str, NormalizedJobSkill] = {}

    for item in skills:
        raw_name = ""
        hint_cat = None
        priority: RequirementPriority = "must_have"
        minimum_years: Optional[float] = None
        evidence: Optional[str] = None

        if isinstance(item, JobSkillRequirement):
            raw_name = item.name
            hint_cat = item.category
            priority = item.priority
            minimum_years = item.minimum_years
            evidence = item.evidence
        elif isinstance(item, dict):
            raw_name = item.get("name", "")
            hint_cat = item.get("category")
            priority = item.get("priority", "must_have")
            minimum_years = item.get("minimum_years")
            evidence = item.get("evidence")
        elif isinstance(item, str):
            raw_name = item

        norm_base = normalize_skill(raw_name, hint_category=hint_cat, source=source)
        if norm_base is None:
            continue

        clean_evidence = evidence.strip() if (evidence and isinstance(evidence, str)) else None

        job_skill = NormalizedJobSkill(
            canonical_name=norm_base.canonical_name,
            original_name=norm_base.original_name,
            original_names=list(norm_base.original_names),
            category=norm_base.category,
            priority=priority,
            minimum_years=minimum_years,
            evidence=clean_evidence,
            normalization_method=norm_base.normalization_method,
            confidence=norm_base.confidence,
            source=source,
        )

        key = job_skill.canonical_name.lower()
        if key not in dedup_map:
            dedup_map[key] = job_skill
        else:
            existing = dedup_map[key]
            # Merge original names
            for oname in job_skill.original_names:
                if oname not in existing.original_names:
                    existing.original_names.append(oname)

            # Priority precedence: must_have trumps nice_to_have
            if job_skill.priority == "must_have":
                existing.priority = "must_have"

            # Minimum years precedence: take maximum required years
            if job_skill.minimum_years is not None:
                if existing.minimum_years is None or job_skill.minimum_years > existing.minimum_years:
                    existing.minimum_years = job_skill.minimum_years

            # Combine distinct evidence
            if clean_evidence:
                if not existing.evidence:
                    existing.evidence = clean_evidence
                elif clean_evidence not in existing.evidence:
                    existing.evidence = f"{existing.evidence}; {clean_evidence}"

            # Category preference
            if existing.category == "other" and job_skill.category != "other":
                existing.category = job_skill.category

            # Method preference
            if job_skill.confidence > existing.confidence:
                existing.confidence = job_skill.confidence
                existing.normalization_method = job_skill.normalization_method

    return list(dedup_map.values())
