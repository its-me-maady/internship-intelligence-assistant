from app.models.analysis_models import (
    JobRequirementsSchema,
    SkillGapAnalysisRequest,
    SkillGapAnalysisResponse,
)
from app.services.document_service import document_service
from app.services.extraction_service import extraction_service
from app.services.matching_service import matching_service
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


@router.post(
    "/skill-gap",
    response_model=SkillGapAnalysisResponse,
    summary="Perform deterministic skill gap and match scoring analysis",
    description=(
        "Evaluates candidate skills against must-have and nice-to-have "
        "requirements. If extracted_requirements is supplied, executes "
        "with 0 LLM calls."
    ),
)
async def analyze_skill_gap(
    request: SkillGapAnalysisRequest,
) -> SkillGapAnalysisResponse:
    """Performs deterministic gap analysis and generates prioritized roadmap."""
    # If pre-extracted requirements are provided, evaluate with 0 LLM calls
    if request.extracted_requirements is not None:
        return matching_service.analyze_skill_gap(
            job_requirements=request.extracted_requirements,
            user_skills=request.get_skills(),
        )

    # Fallback to document lookup and extraction
    if not request.document_id:
        raise HTTPException(
            status_code=400,
            detail="Either 'document_id' or 'extracted_requirements' must be provided.",
        )

    parsed_doc = document_service.get_parsed_document(request.document_id)
    if not parsed_doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.document_id}' not found.",
        )

    # Perform LLM structured extraction on the document raw text
    job_requirements = extraction_service.extract_job_requirements(parsed_doc.raw_text)

    # Perform deterministic matching analysis
    return matching_service.analyze_skill_gap(
        job_requirements=job_requirements,
        user_skills=request.get_skills(),
    )
