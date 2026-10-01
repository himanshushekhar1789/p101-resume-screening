"""
REST API routes for Skill-Gap Analysis & Evidence Grounding Engine (Phase 9).
"""

import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status

from backend.app.schemas import (
    SkillGapAnalyzeRequest,
    CandidateJobSkillGapResponse,
)
from backend.app.services.skill_gap_analyzer import analyze_skill_gaps
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

router = APIRouter(prefix="/gaps", tags=["Skill-Gap Analysis"])


@router.post(
    "/analyze",
    response_model=CandidateJobSkillGapResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Candidate Skill Gaps & Evidence Grounding",
    description=(
        "Evaluates candidate background against job requirements to identify, ground, and explain "
        "satisfied, missing, insufficient, and not_evaluable skills with transparent evidence citations. "
        "Separates general career experience gaps from technical skill gaps. Does NOT rank or make hiring decisions."
    ),
)
async def analyze_skill_gaps_endpoint(payload: SkillGapAnalyzeRequest):
    """
    Accepts structured CandidateProfile and JobProfile, evaluates all requirements,
    and returns a CandidateJobSkillGapResponse.
    """
    try:
        result = analyze_skill_gaps(
            candidate=payload.candidate,
            job=payload.job,
            include_semantic=payload.include_semantic if payload.include_semantic is not None else True,
        )
        if payload.candidate_id:
            result.candidate_id = payload.candidate_id
        if payload.job_id:
            result.job_id = payload.job_id
        return result
    except Exception as e:
        logger.error(f"Error during skill gap analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while evaluating skill gaps: {str(e)}",
        )


@router.post(
    "/from-files",
    response_model=CandidateJobSkillGapResponse,
    status_code=status.HTTP_200_OK,
    summary="End-to-End Skill Gap Analysis from uploaded resume and JD documents",
    description=(
        "Accepts a candidate resume (.pdf/.docx) and a job description document (.pdf/.docx), "
        "runs the end-to-end extraction and normalization pipeline, and performs skill-gap analysis "
        "with evidence grounding and transparent explanations."
    ),
)
async def gaps_from_files_endpoint(
    resume_file: UploadFile = File(..., description="Candidate resume (PDF or DOCX)"),
    job_file: UploadFile = File(..., description="Job description (PDF or DOCX)"),
    include_semantic: bool = True,
):
    """
    Convenience endpoint accepting uploaded documents for both resume and JD,
    parsing, extracting, and analyzing skill gaps in a single workflow.
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

        result = analyze_skill_gaps(
            candidate=candidate_profile,
            job=job_profile,
            include_semantic=include_semantic,
        )
        result.candidate_id = resume_file.filename
        result.job_id = job_file.filename
        return result
    except (UnsupportedFormatError, EmptyDocumentError, CorruptDocumentError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ScannedDocumentError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DocumentSizeLimitError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
    except Exception as e:
        logger.error(f"Error during skill gap analysis from files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while analyzing skill gaps from files: {str(e)}",
        )
