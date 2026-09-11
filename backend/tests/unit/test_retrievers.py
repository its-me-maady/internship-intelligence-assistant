import pytest
from app.models.document_models import DocumentChunk
from app.rag.retrievers import DocumentRetriever
from app.services.vector_service import ChromaVectorStore
from tests.conftest import FakeEmbeddingService


class TestDocumentRetriever:
    """Unit tests for DocumentRetriever filtering and top-k retrieval."""

    @pytest.fixture
    def populated_retriever(self, tmp_path):
        persist_dir = str(tmp_path / "test_retriever_chroma")
        store = ChromaVectorStore(
            persist_directory=persist_dir,
            collection_name="test_retriever_collection",
            embedding_service=FakeEmbeddingService(dimension=16),
        )
        chunks = [
            DocumentChunk(
                chunk_id="chunk-1",
                document_id="doc-alpha",
                filename="alpha_job.pdf",
                content="Python backend intern role requiring FastAPI and PostgreSQL.",
                chunk_index=0,
                page_number=1,
                character_start=0,
                character_end=60,
                total_chunks=2,
                uploaded_at="2026-09-11T10:00:00Z",
            ),
            DocumentChunk(
                chunk_id="chunk-2",
                document_id="doc-alpha",
                filename="alpha_job.pdf",
                content="Responsibilities include optimizing SQL DBs and REST APIs.",
                chunk_index=1,
                page_number=2,
                character_start=61,
                character_end=130,
                total_chunks=2,
                uploaded_at="2026-09-11T10:00:00Z",
            ),
            DocumentChunk(
                chunk_id="chunk-3",
                document_id="doc-beta",
                filename="beta_job.docx",
                content="Frontend developer intern role requiring React and TS.",
                chunk_index=0,
                page_number=1,
                character_start=0,
                character_end=68,
                total_chunks=1,
                uploaded_at="2026-09-11T10:05:00Z",
            ),
        ]
        store.add_chunks(chunks)
        return DocumentRetriever(vector_store=store)

    def test_retrieve_returns_top_k_chunks(self, populated_retriever):
        results = populated_retriever.retrieve(query="Python backend", top_k=2)
        assert len(results) <= 2
        assert len(results) > 0
        assert all(hasattr(r, "page_content") for r in results)

    def test_retrieve_respects_document_id_filter(self, populated_retriever):
        results = populated_retriever.retrieve(
            query="developer intern", top_k=5, document_id="doc-beta"
        )
        assert len(results) == 1
        assert results[0].metadata["document_id"] == "doc-beta"
        assert results[0].metadata["filename"] == "beta_job.docx"

    def test_retrieve_with_nonexistent_document_id_returns_empty(
        self, populated_retriever
    ):
        results = populated_retriever.retrieve(
            query="Python", top_k=5, document_id="non-existent-doc"
        )
        assert results == []

    def test_retrieve_empty_store_returns_empty_list(self, tmp_path):
        empty_store = ChromaVectorStore(
            persist_directory=str(tmp_path / "empty_chroma"),
            collection_name="empty_collection",
            embedding_service=FakeEmbeddingService(dimension=16),
        )
        retriever = DocumentRetriever(vector_store=empty_store)
        results = retriever.retrieve(query="anything", top_k=4)
        assert results == []
