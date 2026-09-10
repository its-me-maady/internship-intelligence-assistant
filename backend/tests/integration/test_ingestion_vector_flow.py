import hashlib
from typing import List

from app.main import app
from app.services.document_service import document_service
from app.services.vector_service import ChromaVectorStore, EmbeddingService
from fastapi.testclient import TestClient


class FakeEmbeddingService(EmbeddingService):
    """Deterministic offline embedding for integration tests."""

    def __init__(self, dimension: int = 16):
        self.dimension = dimension

    def _embed(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [
            float((digest[i % len(digest)] % 100) / 100.0)
            for i in range(self.dimension)
        ]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


def test_full_upload_embed_and_delete_flow(tmp_path, monkeypatch):
    test_chroma_dir = str(tmp_path / "integration_chroma")
    fake_store = ChromaVectorStore(
        persist_directory=test_chroma_dir,
        collection_name="test_integration_flow",
        embedding_service=FakeEmbeddingService(dimension=16),
    )

    monkeypatch.setattr("app.main.get_vector_store", lambda: fake_store)
    monkeypatch.setattr(
        "app.services.document_service.get_vector_store", lambda: fake_store
    )
    document_service._vector_store = fake_store

    client = TestClient(app)

    # 1. Initial health check
    health_initial = client.get("/health").json()
    assert health_initial["indexed_documents_count"] == 0
    assert health_initial["total_chunks_count"] == 0

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
    assert health_after_upload["indexed_documents_count"] == 1
    assert health_after_upload["total_chunks_count"] == chunk_count

    # 4. Delete document
    delete_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    # 5. Health check reflects reduction in indexed counts
    health_after_delete = client.get("/health").json()
    assert health_after_delete["indexed_documents_count"] == 0
    assert health_after_delete["total_chunks_count"] == 0
