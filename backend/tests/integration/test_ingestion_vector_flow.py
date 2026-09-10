from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_full_upload_embed_and_delete_flow():
    # 1. Initial health check
    health_initial = client.get("/health").json()
    init_docs = health_initial.get("indexed_documents_count", 0)
    init_chunks = health_initial.get("total_chunks_count", 0)

    # 2. Upload a document
    content = (
        b"Role: Machine Learning Intern\n"
        b"Responsibilities:\n"
        b"- Train deep neural networks using PyTorch and TensorFlow\n"
        b"- Implement RAG vector search pipelines with ChromaDB\n"
        b"- Optimize GPU inference latency"
    )
    files = {"file": ("ml_intern.txt", content, "text/plain")}
    upload_res = client.post("/api/v1/documents/upload", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]
    chunk_count = upload_res.json()["chunk_count"]
    assert chunk_count >= 1

    # 3. Health check reflects new indexed counts
    health_after_upload = client.get("/health").json()
    assert health_after_upload["indexed_documents_count"] == init_docs + 1
    assert health_after_upload["total_chunks_count"] == init_chunks + chunk_count

    # 4. Delete document
    delete_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    # 5. Health check reflects reduction in indexed counts
    health_after_delete = client.get("/health").json()
    assert health_after_delete["indexed_documents_count"] == init_docs
    assert health_after_delete["total_chunks_count"] == init_chunks
