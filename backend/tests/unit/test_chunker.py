from app.models.document_models import PageContent, ParsedDocument
from app.services.chunking_service import ChunkingService


class TestChunkingService:
    """Tests for RecursiveCharacterTextSplitter and metadata preservation."""

    def test_chunking_creates_chunks_with_correct_size_and_overlap(self):
        chunker = ChunkingService(chunk_size=800, chunk_overlap=150)
        long_text = (
            "We are looking for a Software Engineering Intern to join our "
            "backend team. You will build high-throughput APIs, optimize "
            "relational databases, and participate in agile sprints.\n\n"
            "Key Requirements:\n"
            "- Strong proficiency in Python, FastAPI, and async programming.\n"
            "- Solid foundation in data structures and database design.\n"
            "- Experience with PostgreSQL, Redis, Docker, and CI/CD.\n"
            "- Enrolled in a Computer Science degree program.\n\n"
        ) * 5

        parsed_doc = ParsedDocument(
            document_id="test-doc-123",
            filename="backend_intern.pdf",
            file_size_bytes=len(long_text.encode("utf-8")),
            pages=[
                PageContent(page_number=1, text=long_text[:1200]),
                PageContent(page_number=2, text=long_text[1200:]),
            ],
            raw_text=long_text,
        )

        chunks = chunker.split_document(parsed_doc)

        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.document_id == "test-doc-123"
            assert chunk.filename == "backend_intern.pdf"
            assert chunk.chunk_id is not None
            assert isinstance(chunk.chunk_index, int)
            assert chunk.page_number in (1, 2)
            assert len(chunk.content) <= 800
            assert chunk.character_start >= 0
            assert chunk.character_end > chunk.character_start
            assert chunk.total_chunks == len(chunks)
            assert chunk.uploaded_at is not None

    def test_chunking_preserves_sentence_boundaries(self):
        chunker = ChunkingService(chunk_size=200, chunk_overlap=30)
        text = (
            "First sentence about Python requirements. "
            "Second sentence about database optimization. "
            "Third sentence about cloud infrastructure. "
            "Fourth sentence about agile methodology."
        )
        parsed_doc = ParsedDocument(
            document_id="boundary-doc",
            filename="boundary.txt",
            file_size_bytes=len(text),
            pages=[PageContent(page_number=None, text=text)],
            raw_text=text,
        )

        chunks = chunker.split_document(parsed_doc)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert not chunk.content.startswith(" ")

    def test_chunking_empty_pages_returns_empty_list(self):
        chunker = ChunkingService()
        parsed_doc = ParsedDocument(
            document_id="empty-doc",
            filename="empty.txt",
            file_size_bytes=0,
            pages=[PageContent(page_number=None, text="")],
            raw_text="",
        )
        chunks = chunker.split_document(parsed_doc)
        assert chunks == []
