import pytest
from app.models.document_models import DocumentChunk
from app.services.vector_service import (
    ChromaVectorStore,
    EmbeddingServiceFactory,
    GeminiEmbeddingService,
    LocalMiniLMEmbeddingService,
)
from tests.conftest import FakeEmbeddingService


class TestEmbeddingServiceAbstraction:
    """Tests for embedding abstraction factory and provider instantiation."""

    def test_factory_creates_local_embedding_service(self):
        service = EmbeddingServiceFactory.get_embedding_service("local")
        assert isinstance(service, LocalMiniLMEmbeddingService)
        assert service.model_name == "sentence-transformers/all-MiniLM-L6-v2"

    def test_factory_creates_gemini_embedding_service(self):
        service = EmbeddingServiceFactory.get_embedding_service(
            "gemini", api_key="fake-key-for-test"
        )
        assert isinstance(service, GeminiEmbeddingService)
        assert service.model == "models/text-embedding-004"

    def test_factory_raises_for_invalid_provider(self):
        with pytest.raises(ValueError, match="Unsupported embedding provider"):
            EmbeddingServiceFactory.get_embedding_service("invalid_provider")

    def test_fake_embedding_service_is_deterministic(self):
        fake = FakeEmbeddingService(dimension=8)
        vec1 = fake.embed_query("Python")
        vec2 = fake.embed_query("Python")
        assert vec1 == vec2
        assert len(vec1) == 8


class TestChromaVectorStore:
    """Tests for ChromaVectorStore chunk indexing, querying, and deletion."""

    @pytest.fixture
    def vector_store(self, tmp_path):
        persist_dir = str(tmp_path / "test_chroma")
        embedding_service = FakeEmbeddingService(dimension=16)
        return ChromaVectorStore(
            persist_directory=persist_dir,
            collection_name="test_internship_documents",
            embedding_service=embedding_service,
        )

    def test_add_and_query_chunks(self, vector_store):
        chunks = [
            DocumentChunk(
                chunk_id="c1",
                document_id="doc-1",
                filename="job1.pdf",
                content="Requires strong Python and FastAPI development skills.",
                chunk_index=0,
                page_number=1,
                character_start=0,
                character_end=53,
                total_chunks=2,
                uploaded_at="2026-09-10T14:00:00Z",
            ),
            DocumentChunk(
                chunk_id="c2",
                document_id="doc-1",
                filename="job1.pdf",
                content="Experience with PostgreSQL database optimization and Docker.",
                chunk_index=1,
                page_number=2,
                character_start=55,
                character_end=115,
                total_chunks=2,
                uploaded_at="2026-09-10T14:00:00Z",
            ),
        ]

        vector_store.add_chunks(chunks)
        assert vector_store.get_total_chunks_count() == 2
        assert vector_store.get_indexed_documents_count() == 1

        # Query relevant chunks
        results = vector_store.similarity_search(query="Python API programming", k=1)
        assert len(results) == 1
        assert results[0].metadata["chunk_id"] == "c1"
        assert "FastAPI" in results[0].page_content

    def test_delete_document_removes_all_chunks(self, vector_store):
        chunks_doc1 = [
            DocumentChunk(
                chunk_id="c1",
                document_id="doc-1",
                filename="job1.pdf",
                content="Python skills.",
                chunk_index=0,
                page_number=1,
                character_start=0,
                character_end=14,
                total_chunks=1,
                uploaded_at="2026-09-10T14:00:00Z",
            )
        ]
        chunks_doc2 = [
            DocumentChunk(
                chunk_id="c2",
                document_id="doc-2",
                filename="job2.pdf",
                content="React skills.",
                chunk_index=0,
                page_number=1,
                character_start=0,
                character_end=13,
                total_chunks=1,
                uploaded_at="2026-09-10T14:00:00Z",
            )
        ]

        vector_store.add_chunks(chunks_doc1)
        vector_store.add_chunks(chunks_doc2)

        assert vector_store.get_total_chunks_count() == 2
        assert vector_store.get_indexed_documents_count() == 2

        # Delete doc-1
        deleted_count = vector_store.delete_document("doc-1")
        assert deleted_count == 1
        assert vector_store.get_total_chunks_count() == 1
        assert vector_store.get_indexed_documents_count() == 1

        # Verify doc-1 chunks are no longer returned in query
        results = vector_store.similarity_search("Python", k=2)
        assert all(r.metadata["document_id"] != "doc-1" for r in results)
