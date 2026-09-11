from app.main import app
from app.models.analysis_models import JobRequirementsSchema
from app.services.document_service import document_service
from fastapi.testclient import TestClient

client = TestClient(app)


def test_matching_api_skill_gap_with_pre_extracted_data_success():
    """Tests skill-gap with pre-extracted requirements (0 LLM calls)."""
    extracted = JobRequirementsSchema(
        job_title="Backend Engineer Intern",
        company_name="Cloud Corp",
        required_technical_skills=["Python", "FastAPI", "PostgreSQL", "Git"],
        preferred_technical_skills=["Docker", "Kubernetes"],
        raw_summary="Backend intern role focusing on Python APIs.",
    )
    # Candidate: Python, Git, PostgreSQL (3/4 = 75%), Docker (1/2 = 50%)
    # Expected: (0.75 * 70) + (0.50 * 30) = 67.5%
    payload = {
        "user_skills": ["Python", "Git", "PostgreSQL", "Docker"],
        "extracted_requirements": extracted.model_dump(),
    }
    response = client.post("/api/v1/analysis/skill-gap", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["match_score_percentage"] == 67.5
    assert set(data["matched_required_skills"]) == {"Python", "Git", "PostgreSQL"}
    assert data["missing_required_skills"] == ["FastAPI"]
    assert data["matched_preferred_skills"] == ["Docker"]
    assert data["missing_preferred_skills"] == ["Kubernetes"]

    # Roadmap ordering: Critical Required must precede High-Value Preferred
    roadmap = data["priority_learning_roadmap"]
    assert len(roadmap) == 2
    assert roadmap[0]["skill"] == "FastAPI"
    assert roadmap[0]["category"] == "Critical Required"
    assert roadmap[1]["skill"] == "Kubernetes"
    assert roadmap[1]["category"] == "High-Value Preferred"


def test_matching_api_skill_gap_fallback_to_document_id():
    """Tests skill-gap fallback when only document_id is supplied."""
    jd_text = """
    Job Title: Machine Learning Research Intern
    Company: Neural Systems Inc.
    Location: Mountain View, CA / Hybrid
    Required Skills: Python, PyTorch, Transformers
    Preferred Skills: CUDA, Triton, Ray
    Responsibilities: Conduct deep learning evaluations
    """
    upload_res = document_service.process_and_store_document(
        filename="ml_intern_jd.txt",
        content=jd_text.encode("utf-8"),
    )
    doc_id = upload_res.document_id

    # Fake LLM provides:
    # required_technical_skills: ["Python", "PyTorch", "Transformers"]
    # preferred_technical_skills: ["CUDA", "Triton", "Ray"]
    payload = {
        "document_id": doc_id,
        "user_skills": ["python", "cuda"],
    }
    response = client.post("/api/v1/analysis/skill-gap", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert round(data["match_score_percentage"], 1) == 33.3
    assert data["matched_required_skills"] == ["Python"]
    assert data["missing_required_skills"] == ["PyTorch", "Transformers"]
    assert data["matched_preferred_skills"] == ["CUDA"]
    assert data["missing_preferred_skills"] == ["Triton", "Ray"]


def test_matching_api_missing_both_document_id_and_extracted_data():
    """Tests skill-gap returns 400 if neither ID nor requirements given."""
    payload = {
        "user_skills": ["Python"],
    }
    response = client.post("/api/v1/analysis/skill-gap", json=payload)
    assert response.status_code == 400
    assert (
        "either 'document_id' or 'extracted_requirements'"
        in response.json()["detail"].lower()
    )


def test_matching_api_document_not_found():
    """Tests POST /api/v1/analysis/skill-gap returns 404 for unknown document_id."""
    payload = {
        "document_id": "non-existent-uuid",
        "user_skills": ["Python"],
    }
    response = client.post("/api/v1/analysis/skill-gap", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
