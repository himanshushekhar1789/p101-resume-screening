"""
REST API routes for Candidate ↔ Job Requirement Matching Engine (Phase 6).
"""

import logging
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, status

from backend.app.schemas import (
    MatchingAnalyzeRequest,
    CandidateJobMatchResponse,
    CandidateJobSemanticMatchResponse,
)
from backend.app.services.matching_engine import MatchingEngine
from backend.app.services.document_parser import (
    parse_document,
    UnsupportedFormatError,
    EmptyDocumentError,
    ScannedDocumentError,
    CorruptDocumentError,
    DocumentSizeLimitError,
)
from backend.app.services.resume_extractor import extract_candidate_profile
from backend.app.services.jd_analyzer import analyze_job_description

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matching", tags=["Candidate ↔ Job Matching"])


@router.post(
    "/analyze",
    response_model=CandidateJobMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Match Candidate Profile against Job Profile",
    description=(
        "Performs deterministic, requirement-by-requirement evaluation of a candidate profile "
        "against job description requirements, returning structured match status, match method, "
        "evidence citations, and requirement breakdown. Optionally includes Phase 7 semantic matching."
    ),
)
async def analyze_match_endpoint(payload: MatchingAnalyzeRequest):
    """
    Accepts structured CandidateProfile and JobProfile, evaluates all requirements,
    and returns a CandidateJobMatchResponse.
    """
    try:
        engine = MatchingEngine()
        result = engine.match_candidate_to_job(
            candidate=payload.candidate,
            job=payload.job,
            candidate_id=payload.candidate_id,
            job_id=payload.job_id,
            include_semantic=payload.include_semantic or False,
        )
        return result
    except Exception as e:
        logger.error(f"Error during candidate-job matching: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while evaluating candidate against job requirements: {str(e)}",
        )


@router.post(
    "/semantic",
    response_model=CandidateJobSemanticMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Semantic Candidate ↔ Requirement Matching",
    description=(
        "Evaluates contextual conceptual similarity between candidate evidence and job requirements "
        "using local SentenceTransformer embeddings and cosine similarity. Does not compute hiring scores."
    ),
)
async def semantic_match_endpoint(payload: MatchingAnalyzeRequest):
    """
    Evaluates semantic similarity between candidate profile evidence and job description requirements.
    """
    from backend.app.config import get_settings
    settings = get_settings()

    if not settings.semantic_matching_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Semantic matching is disabled by configuration (SEMANTIC_MATCHING_ENABLED=False).",
        )

    try:
        from backend.app.services.semantic_matcher import evaluate_semantic_matches
        result = evaluate_semantic_matches(candidate=payload.candidate, job=payload.job)
        result.candidate_id = payload.candidate_id
        result.job_id = payload.job_id
        return result
    except Exception as e:
        logger.error(f"Error during semantic matching: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while executing semantic matching: {str(e)}",
        )


@router.post(
    "/from-files",
    response_model=CandidateJobMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="End-to-End matching from uploaded resume and JD documents",
    description=(
        "Accepts a candidate resume (.pdf/.docx) and a job description document (.pdf/.docx), "
        "runs the end-to-end extraction and normalization pipeline, and performs deterministic matching."
    ),
)
async def match_from_files_endpoint(
    resume_file: UploadFile = File(..., description="Candidate resume (PDF or DOCX)"),
    job_file: UploadFile = File(..., description="Job description (PDF or DOCX)"),
    include_semantic: bool = False,
):
    """
    Convenience endpoint accepting uploaded documents for both resume and JD,
    parsing, extracting, and matching them in a single workflow.
    """
    if not resume_file.filename or not job_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing from one of the uploaded files.",
        )

    try:
        resume_bytes = await resume_file.read()
        job_bytes = await job_file.read()

        parsed_resume = parse_document(resume_bytes, resume_file.filename)
        parsed_job = parse_document(job_bytes, job_file.filename)

        candidate_profile = await extract_candidate_profile(parsed_resume.text)
        job_profile = await analyze_job_description(parsed_job.text)

        engine = MatchingEngine()
        return engine.match_candidate_to_job(
            candidate=candidate_profile,
            job=job_profile,
            candidate_id=resume_file.filename,
            job_id=job_file.filename,
            include_semantic=include_semantic,
        )
    except (UnsupportedFormatError, EmptyDocumentError, CorruptDocumentError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ScannedDocumentError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DocumentSizeLimitError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
    except Exception as e:
        logger.error(f"Error during matching from files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while matching from files: {str(e)}",
        )
