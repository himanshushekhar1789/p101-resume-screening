import logging
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from backend.app.config import get_settings
from backend.app.schemas import (
    JobAnalysisRequest,
    JobAnalysisResponse,
    JobAnalysisMetadata,
)
from backend.app.services.document_parser import (
    parse_document,
    UnsupportedFormatError,
    EmptyDocumentError,
    ScannedDocumentError,
    CorruptDocumentError,
    DocumentSizeLimitError,
)
from backend.app.services.jd_analyzer import analyze_job_description
from backend.app.ai.validators import LLMValidationError
from backend.app.ai.llm_client import LLMError, LLMUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Job Description Analysis"])


@router.post(
    "/analyze",
    response_model=JobAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze job description from raw text",
    description=(
        "Analyzes a plain text job description to extract structured, validated job requirements, "
        "including must-have vs nice-to-have classification, skills, experience, education, certifications, and responsibilities."
    ),
)
async def analyze_job_text(payload: JobAnalysisRequest):
    """
    Accept raw job description text via JSON body, extract structured requirements,
    and return a validated JobProfile.
    """
    if not payload.job_description or not payload.job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text cannot be empty.",
        )

    settings = get_settings()

    try:
        profile = await analyze_job_description(
            raw_text=payload.job_description,
            initial_title=payload.job_title,
        )
    except LLMUnavailableError as e:
        logger.error(f"LLM service unavailable during JD analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}",
        )
    except (LLMValidationError, LLMError) as e:
        logger.error(f"LLM processing error during JD analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI generation failed: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error during JD analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while analyzing the job description.",
        )

    char_count = len(payload.job_description)
    word_count = len(payload.job_description.split())

    return JobAnalysisResponse(
        job_title=profile.job_title,
        profile=profile,
        metadata=JobAnalysisMetadata(
            character_count=char_count,
            word_count=word_count,
            source_type="text",
            llm_provider=settings.llm_provider,
        ),
    )


@router.post(
    "/analyze/upload",
    response_model=JobAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze job description from uploaded PDF/DOCX file",
    description=(
        "Uploads a PDF or DOCX job description, extracts text using the Phase 2 document parser, "
        "and produces a validated JobProfile with requirement classification."
    ),
)
async def analyze_job_file(
    file: UploadFile = File(...),
    job_title: Optional[str] = Form(None),
):
    """
    Accept an uploaded JD document (.pdf or .docx), parse its text via document_parser,
    and return a structured and validated JobProfile.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing from the uploaded file.",
        )

    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read uploaded file payload.",
        )

    # Step 1: Document Parsing & Validation
    try:
        parsed_doc = parse_document(file_bytes=file_bytes, filename=file.filename)
    except UnsupportedFormatError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except EmptyDocumentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ScannedDocumentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except CorruptDocumentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DocumentSizeLimitError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))

    # Step 2: Structured Job Profile Extraction
    settings = get_settings()
    try:
        profile = await analyze_job_description(
            raw_text=parsed_doc.text,
            initial_title=job_title,
        )
    except LLMUnavailableError as e:
        logger.error(f"LLM service unavailable during uploaded JD analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}",
        )
    except (LLMValidationError, LLMError) as e:
        logger.error(f"LLM processing error during uploaded JD analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI generation failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during uploaded JD analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while analyzing the uploaded job description.",
        )

    return JobAnalysisResponse(
        job_title=profile.job_title,
        profile=profile,
        metadata=JobAnalysisMetadata(
            character_count=parsed_doc.character_count,
            word_count=parsed_doc.word_count,
            source_type=parsed_doc.file_type,
            llm_provider=settings.llm_provider,
        ),
    )
