from app.models.analysis_models import JobRequirementsSchema
from app.services.document_service import document_service
from app.services.extraction_service import extraction_service
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post(
    "/extract/{document_id}",
    response_model=JobRequirementsSchema,
    summary="Extract structured internship requirements",
    description=(
        "Extracts structured job parameters, skills, and qualifications "
        "from an ingested document using LLM structured output."
    ),
)
async def extract_document_requirements(document_id: str) -> JobRequirementsSchema:
    """Fetches document by ID and extracts structured JobRequirementsSchema."""
    parsed_doc = document_service.get_parsed_document(document_id)
    if not parsed_doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID '{document_id}' not found.",
        )

    return extraction_service.extract_job_requirements(parsed_doc.raw_text)
