from app.main import app
from app.services.document_service import document_service
from fastapi.testclient import TestClient

client = TestClient(app)


def test_matching_api_skill_gap_success():
    """Tests POST /api/v1/analysis/skill-gap returns computed scores and roadmap."""
    # 1. Ingest a document
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

    # 2. Call skill-gap analysis endpoint
    # Fake LLM in conftest provides:
    # required_technical_skills: ["Python", "PyTorch", "Transformers"]
    # preferred_technical_skills: ["CUDA", "Triton", "Ray"]
    # Student provides: ["python", "cuda"] (1/3 required, 1/3 preferred)
    # Expected score: (1/3 * 70) + (1/3 * 30) = 23.33 + 10.0 = 33.33 -> 33.3%
    payload = {
        "document_id": doc_id,
        "user_skills": ["python", "cuda"],
    }
    response = client.post("/api/v1/analysis/skill-gap", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "match_score_percentage" in data
    assert round(data["match_score_percentage"], 1) == 33.3
    assert data["matched_required_skills"] == ["Python"]
    assert data["missing_required_skills"] == ["PyTorch", "Transformers"]
    assert data["matched_preferred_skills"] == ["CUDA"]
    assert data["missing_preferred_skills"] == ["Triton", "Ray"]

    # Verify roadmap structure and ordering
    roadmap = data["priority_learning_roadmap"]
    assert len(roadmap) == 4
    assert roadmap[0]["skill"] == "PyTorch"
    assert roadmap[0]["category"] == "Critical Required"
    assert roadmap[1]["skill"] == "Transformers"
    assert roadmap[1]["category"] == "Critical Required"
    assert roadmap[2]["skill"] == "Triton"
    assert roadmap[2]["category"] == "High-Value Preferred"
    assert roadmap[3]["skill"] == "Ray"
    assert roadmap[3]["category"] == "High-Value Preferred"


def test_matching_api_document_not_found():
    """Tests POST /api/v1/analysis/skill-gap returns 404 for unknown document_id."""
    payload = {
        "document_id": "non-existent-uuid",
        "user_skills": ["Python"],
    }
    response = client.post("/api/v1/analysis/skill-gap", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
