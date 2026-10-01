"""
REST API routes for LLM Explanations & Personalized Recommendations (Phase 10).
"""

import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status

from backend.app.schemas import (
    ExplanationAnalyzeRequest,
    LLMExplanationResponse,
)
from backend.app.services.llm_explanation_service import generate_candidate_explanation
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
from backend.app.ai.validators import LLMValidationError
from backend.app.ai.llm_client import LLMUnavailableError, LLMError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/explanations", tags=["LLM Explanations & Recommendations"])


@router.post(
    "/analyze",
    response_model=LLMExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Grounded LLM Explanation & Recommendations",
    description=(
        "Consumes structured candidate and job profiles, runs matching, scoring, and skill-gap engines, "
        "and produces a human-readable explanation and targeted skill-gap improvement recommendations. "
        "Strictly grounded in resume/job facts; does NOT rank candidates or make hiring decisions."
    ),
)
async def analyze_explanation_endpoint(payload: ExplanationAnalyzeRequest):
    """
    Accepts structured profiles or raw texts, executes the complete Phase 6-9 pipeline,
    and returns an evidence-grounded explanation and personalized recommendation report.
    """
    try:
        # Resolve candidate profile
        if payload.candidate is not None:
            candidate_profile = payload.candidate
        elif payload.candidate_text:
            candidate_profile = await extract_candidate_profile(payload.candidate_text)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'candidate' structured profile or 'candidate_text' must be provided.",
            )

        # Resolve job profile
        if payload.job is not None:
            job_profile = payload.job
        elif payload.job_text:
            job_profile = await analyze_job_description(payload.job_text)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'job' structured profile or 'job_text' must be provided.",
            )

        result = await generate_candidate_explanation(
            candidate=candidate_profile,
            job=job_profile,
            candidate_id=payload.candidate_id,
            job_id=payload.job_id,
            scoring_weights=payload.scoring_weights,
            llm_fit_score=payload.llm_fit_score,
            include_semantic=payload.include_semantic if payload.include_semantic is not None else True,
        )
        return result

    except HTTPException:
        raise
    except LLMValidationError as e:
        logger.error(f"LLM schema validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"LLM response failed schema validation: {str(e)}",
        )
    except LLMUnavailableError as e:
        logger.error(f"LLM service unavailable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM provider is currently unavailable: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error during explanation generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating explanation and recommendations: {str(e)}",
        )


@router.post(
    "/from-files",
    response_model=LLMExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="End-to-End Explanation & Recommendations from uploaded files",
    description=(
        "Accepts a candidate resume (.pdf/.docx) and a job description document (.pdf/.docx), "
        "runs the end-to-end extraction, matching, scoring, and skill-gap pipeline, and returns "
        "a grounded explanation and personalized recommendations report."
    ),
)
async def explanation_from_files_endpoint(
    resume_file: UploadFile = File(..., description="Candidate resume (PDF or DOCX)"),
    job_file: UploadFile = File(..., description="Job description (PDF or DOCX)"),
    include_semantic: bool = True,
):
    """
    Convenience endpoint accepting uploaded documents for both resume and JD,
    executing end-to-end parsing, extraction, scoring, gap analysis, and LLM explanation.
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

        result = await generate_candidate_explanation(
            candidate=candidate_profile,
            job=job_profile,
            candidate_id=resume_file.filename,
            job_id=job_file.filename,
            include_semantic=include_semantic,
        )
        return result

    except (UnsupportedFormatError, EmptyDocumentError, CorruptDocumentError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ScannedDocumentError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DocumentSizeLimitError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
    except LLMValidationError as e:
        logger.error(f"LLM schema validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"LLM response failed schema validation: {str(e)}",
        )
    except LLMUnavailableError as e:
        logger.error(f"LLM service unavailable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM provider is currently unavailable: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error during explanation from files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating explanation from files: {str(e)}",
        )
