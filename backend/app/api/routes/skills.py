import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas import (
    SkillNormalizeRequest,
    SkillNormalizeResponse,
    NormalizedSkill,
)
from backend.app.services.skill_normalizer import normalize_candidate_skills
from backend.app.services.skill_taxonomy import (
    get_all_canonical_skills,
    get_taxonomy_categories,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/skills", tags=["Skill Normalization & Taxonomy"])


@router.post(
    "/normalize",
    response_model=SkillNormalizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Normalize and deduplicate raw skills",
    description=(
        "Transforms a list of raw skill strings into canonical, deduplicated skills with "
        "taxonomy categorization, alias resolution, version normalization, and provenance tracking."
    ),
)
async def normalize_skills_endpoint(payload: SkillNormalizeRequest):
    """
    Accept a list of raw skill strings, normalize each against the canonical taxonomy registry,
    deduplicate, and return the canonical representation.
    """
    if not payload.skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skills list cannot be empty.",
        )

    try:
        normalized = normalize_candidate_skills(payload.skills, source=payload.source or "manual")
        return SkillNormalizeResponse(
            count=len(normalized),
            normalized_skills=normalized,
        )
    except Exception as e:
        logger.error(f"Unexpected error during skill normalization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while normalizing skills.",
        )


@router.get(
    "/taxonomy",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get canonical skill taxonomy registry",
    description="Returns the full canonical skill registry, categories, and registered aliases.",
)
async def get_taxonomy_endpoint():
    """Return categories and all registered canonical skills."""
    return {
        "categories": get_taxonomy_categories(),
        "canonical_skills_count": len(get_all_canonical_skills()),
        "skills": get_all_canonical_skills(),
    }
