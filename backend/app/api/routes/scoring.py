"""
REST API routes for Multi-Layer Hybrid Fusion Scoring Engine (Phase 8).
"""

import logging
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas import (
    ScoringAnalyzeRequest,
    CandidateJobScoreResponse,
)
from backend.app.services.scoring_engine import get_scoring_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scoring", tags=["Hybrid Fusion Scoring"])


@router.post(
    "/analyze",
    response_model=CandidateJobScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Hybrid Candidate-Fit Score",
    description=(
        "Combines deterministic rule fit (Phase 6), semantic similarity fit (Phase 7), "
        "and verifiable experience tenure into an explainable, configurable candidate-fit score (0.0–1.0). "
        "Does NOT rank candidates, shortlist, or make automated hiring decisions."
    ),
)
async def analyze_scoring_endpoint(payload: ScoringAnalyzeRequest):
    """
    Accepts CandidateProfile and JobProfile, runs matching and semantic evaluation,
    and returns a transparent, multi-layer hybrid score breakdown.
    """
    try:
        engine = get_scoring_engine()
        result = engine.score_candidate_for_job(
            candidate=payload.candidate,
            job=payload.job,
            candidate_id=payload.candidate_id,
            job_id=payload.job_id,
            include_semantic=payload.include_semantic if payload.include_semantic is not None else True,
            weights=payload.weights,
            llm_fit_score=payload.llm_fit_score,
        )
        return result
    except ValueError as e:
        logger.warning(f"Validation error in scoring request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid scoring configuration: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error during candidate-fit scoring: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while computing candidate fit score: {str(e)}",
        )
