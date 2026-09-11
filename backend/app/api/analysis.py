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
        "Evaluates candidate skills against a job description's must-have and "
        "nice-to-have requirements using deterministic weighted scoring and "
        "extensible canonical skill normalization."
    ),
)
async def analyze_skill_gap(
    request: SkillGapAnalysisRequest,
) -> SkillGapAnalysisResponse:
    """Performs deterministic gap analysis and generates prioritized roadmap."""
    parsed_doc = document_service.get_parsed_document(request.document_id)
    if not parsed_doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID '{request.document_id}' not found.",
        )

    job_requirements = extraction_service.extract_job_requirements(parsed_doc.raw_text)
    return matching_service.analyze_skill_gap(
        job_requirements=job_requirements,
        user_skills=request.user_skills,
    )
