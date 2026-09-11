from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_extract_document_success():
    # 1. Upload a realistic JD
    content = (
        b"Role: Machine Learning Research Intern\n"
        b"Company: Neural Systems Inc.\n"
        b"Location: Mountain View, CA / Hybrid\n"
        b"Work Type: Hybrid\n"
        b"Compensation: $60 / hour\n"
        b"Duration: 12 weeks\n"
        b"Required Skills: Python, PyTorch, Transformers\n"
        b"Preferred Skills: CUDA, Triton, Ray\n"
        b"Responsibilities:\n"
        b"- Conduct deep learning model evaluations\n"
        b"- Optimize distributed training pipelines\n"
        b"Summary: 12-week ML research internship on foundation models."
    )
    files = {"file": ("ml_research.txt", content, "text/plain")}
    upload_res = client.post("/api/v1/documents/upload", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # 2. Extract structured requirements via POST /api/v1/analysis/extract/{id}
    extract_res = client.post(f"/api/v1/analysis/extract/{doc_id}")
    assert extract_res.status_code == 200
    data = extract_res.json()

    assert "job_title" in data
    assert "company_name" in data
    assert "required_technical_skills" in data
    assert isinstance(data["required_technical_skills"], list)
    assert "preferred_technical_skills" in data
    assert "key_responsibilities" in data
    assert "raw_summary" in data


def test_extract_document_via_documents_alias_endpoint():
    # Test POST /api/v1/documents/{id}/extract alias
    content = b"Role: Cloud Intern\nCompany: Acme\nSummary: Cloud internship."
    files = {"file": ("cloud.txt", content, "text/plain")}
    upload_res = client.post("/api/v1/documents/upload", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    extract_res = client.post(f"/api/v1/documents/{doc_id}/extract")
    assert extract_res.status_code == 200
    data = extract_res.json()
    assert "job_title" in data
    assert "raw_summary" in data


def test_extract_nonexistent_document_returns_404():
    non_existent = "00000000-0000-0000-0000-000000000000"
    extract_res = client.post(f"/api/v1/analysis/extract/{non_existent}")
    assert extract_res.status_code == 404
    assert "not found" in extract_res.json()["detail"].lower()
