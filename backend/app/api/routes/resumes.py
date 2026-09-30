import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from backend.app.schemas import DocumentParseResponse
from backend.app.services.document_parser import (
    parse_document,
    UnsupportedFormatError,
    EmptyDocumentError,
    ScannedDocumentError,
    CorruptDocumentError,
    DocumentSizeLimitError,
)

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
