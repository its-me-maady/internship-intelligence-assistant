from typing import List

from app.models.document_models import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentSummary,
    DocumentUploadResponse,
)
from app.services.document_service import document_service
from app.services.ingestion_service import DecompressionBombError, FileValidationError
from fastapi import APIRouter, File, HTTPException, UploadFile, status

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse an internship document",
)
async def upload_document(file: UploadFile = File(...)):
    """Uploads, validates, parses, and chunks an internship posting."""
    try:
        content = await file.read()
        return document_service.process_and_store_document(file.filename, content)
    except FileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except DecompressionBombError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"An unexpected error occurred while processing the document: {str(e)}"
            ),
        ) from e


@router.get(
    "",
    response_model=List[DocumentSummary],
    summary="List all uploaded documents",
)
async def list_documents():
    """Returns metadata summaries for all uploaded documents."""
    return document_service.list_documents()


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Retrieve document detail and its chunks",
)
async def get_document(document_id: str):
    """Retrieves full document metadata and its parsed chunks."""
    doc = document_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' was not found.",
        )
    return doc


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete an uploaded document",
)
async def delete_document(document_id: str):
    """Deletes the document and its stored chunks."""
    result = document_service.delete_document(document_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' was not found.",
        )
    return result


@router.post(
    "/{document_id}/extract",
    summary="Extract structured internship requirements (alias)",
)
async def extract_document_alias(document_id: str):
    """Alias for /analysis/extract/{document_id}."""
    from app.api.analysis import extract_document_requirements

    return await extract_document_requirements(document_id)
