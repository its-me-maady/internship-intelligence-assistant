from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_upload_text_document_success():
    content = b"Role: Python Backend Intern\nRequirements:\n- Python\n- SQL\n- FastAPI"
    files = {"file": ("internship.txt", content, "text/plain")}
    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert data["filename"] == "internship.txt"
    assert data["file_size_bytes"] == len(content)
    assert data["page_count"] == 1
    assert data["chunk_count"] >= 1
    assert data["status"] == "READY"
    assert "created_at" in data

    doc_id = data["document_id"]

    # Test GET /api/v1/documents
    list_response = client.get("/api/v1/documents")
    assert list_response.status_code == 200
    docs = list_response.json()
    assert any(d["document_id"] == doc_id for d in docs)

    # Test GET /api/v1/documents/{id}
    detail_response = client.get(f"/api/v1/documents/{doc_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["document_id"] == doc_id
    assert len(detail["chunks"]) >= 1

    # Test DELETE /api/v1/documents/{id}
    delete_response = client.delete(f"/api/v1/documents/{doc_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True

    # Test GET deleted document returns 404
    not_found_response = client.get(f"/api/v1/documents/{doc_id}")
    assert not_found_response.status_code == 404


def test_upload_invalid_extension_returns_400():
    files = {"file": ("malicious.exe", b"binary content", "application/octet-stream")}
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_get_nonexistent_document_returns_404():
    response = client.get("/api/v1/documents/non-existent-uuid")
    assert response.status_code == 404
