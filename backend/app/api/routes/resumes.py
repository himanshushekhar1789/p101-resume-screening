import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from backend.app.config import get_settings
from backend.app.schemas import DocumentParseResponse, ResumeExtractionResponse
from backend.app.services.document_parser import (
    parse_document,
    UnsupportedFormatError,
    EmptyDocumentError,
    ScannedDocumentError,
    CorruptDocumentError,
    DocumentSizeLimitError,
)
from backend.app.services.resume_extractor import extract_candidate_profile
from backend.app.ai.validators import LLMValidationError
from backend.app.ai.llm_client import LLMError, LLMUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resume Processing"])


@router.post(
    "/parse",
    response_model=DocumentParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract text from a PDF or DOCX resume",
    description="Validates and extracts plain text and structural metadata from an uploaded .pdf or .docx resume.",
)
async def parse_resume_document(file: UploadFile = File(...)):
    """
    Accept an uploaded resume document (.pdf or .docx) and return its extracted text.
    Rejects unsupported formats, empty files, corrupt files, and scanned PDFs.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing from the uploaded file.",
        )

    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read uploaded file payload.",
        )

    try:
        parsed = parse_document(file_bytes=file_bytes, filename=file.filename)
        return DocumentParseResponse(
            filename=parsed.filename,
            file_type=parsed.file_type,
            page_count=parsed.page_count,
            character_count=parsed.character_count,
            word_count=parsed.word_count,
            text=parsed.text,
        )
    except UnsupportedFormatError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except EmptyDocumentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ScannedDocumentError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e),
        )
    except CorruptDocumentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except DocumentSizeLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error while parsing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while parsing the document.",
        )


@router.post(
    "/extract",
    response_model=ResumeExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured candidate profile from resume",
    description=(
        "Uploads a PDF or DOCX resume, extracts text, applies rule-based + LLM extraction, "
        "and validates against CandidateProfile."
    ),
)
async def extract_resume_profile(file: UploadFile = File(...)):
    """
    Accept an uploaded resume document (.pdf or .docx), parse its text,
    and return a structured and validated CandidateProfile.
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

    # Step 2: Structured Candidate Profile Extraction
    settings = get_settings()
    try:
        profile = await extract_candidate_profile(parsed_doc.text)
        return ResumeExtractionResponse(
            filename=parsed_doc.filename,
            file_type=parsed_doc.file_type,
            profile=profile,
            extraction_metadata={
                "character_count": parsed_doc.character_count,
                "word_count": parsed_doc.word_count,
                "page_count": parsed_doc.page_count,
                "llm_provider": settings.llm_provider,
            },
        )
    except LLMValidationError as e:
        logger.error(f"LLM validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to extract a valid candidate profile: {str(e)}",
        )
    except LLMUnavailableError as e:
        logger.error(f"LLM provider unavailable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI extraction service is currently unavailable. Please try again later.",
        )
    except Exception as e:
        logger.error(f"Unexpected error during profile extraction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during candidate profile extraction.",
        )

