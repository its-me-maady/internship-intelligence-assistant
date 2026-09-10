from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings
from app.models.document_models import (
    DocumentChunk,
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentStatus,
    DocumentSummary,
    DocumentUploadResponse,
    ParsedDocument,
)
from app.services.chunking_service import ChunkingService
from app.services.ingestion_service import IngestionService
from app.services.vector_service import ChromaVectorStore, vector_store_service


class DocumentService:
    """Coordinates document ingestion, chunking, and vector storage."""

    def __init__(
        self,
        upload_dir: Optional[str] = None,
        ingestion_service: Optional[IngestionService] = None,
        chunking_service: Optional[ChunkingService] = None,
        vector_store: Optional[ChromaVectorStore] = None,
    ):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIRECTORY)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.ingestion_service = ingestion_service or IngestionService(
            max_file_size_mb=settings.MAX_FILE_SIZE_MB
        )
        self.chunking_service = chunking_service or ChunkingService()
        self.vector_store = vector_store or vector_store_service

        # In-memory document storage (persisted across service lifespan)
        self._documents: Dict[str, ParsedDocument] = {}
        self._chunks: Dict[str, List[DocumentChunk]] = {}

    def process_and_store_document(
        self, filename: str, content: bytes
    ) -> DocumentUploadResponse:
        """Validates, parses, chunks, and saves an uploaded document."""
        parsed_doc = self.ingestion_service.validate_and_parse(filename, content)
        chunks = self.chunking_service.split_document(parsed_doc)

        doc_id = parsed_doc.document_id

        # Save raw file on disk safely
        safe_filename = f"{doc_id}_{Path(filename).name}"
        file_path = self.upload_dir / safe_filename
        with open(file_path, "wb") as f:
            f.write(content)

        # Store in registry and vector store
        self._documents[doc_id] = parsed_doc
        self._chunks[doc_id] = chunks
        self.vector_store.add_chunks(chunks)

        return DocumentUploadResponse(
            document_id=doc_id,
            filename=parsed_doc.filename,
            file_size_bytes=parsed_doc.file_size_bytes,
            page_count=parsed_doc.page_count,
            chunk_count=len(chunks),
            status=DocumentStatus.READY,
            created_at=parsed_doc.created_at.isoformat(),
        )

    def list_documents(self) -> List[DocumentSummary]:
        """Returns summary metadata for all registered documents."""
        summaries = []
        for doc_id, doc in self._documents.items():
            chunk_count = len(self._chunks.get(doc_id, []))
            summaries.append(
                DocumentSummary(
                    document_id=doc_id,
                    filename=doc.filename,
                    file_size_bytes=doc.file_size_bytes,
                    page_count=doc.page_count,
                    chunk_count=chunk_count,
                    status=DocumentStatus.READY,
                    created_at=doc.created_at.isoformat(),
                )
            )
        return summaries

    def get_document(self, document_id: str) -> Optional[DocumentDetailResponse]:
        """Retrieves complete document detail including its chunks."""
        doc = self._documents.get(document_id)
        if not doc:
            return None

        chunks = self._chunks.get(document_id, [])
        return DocumentDetailResponse(
            document_id=doc.document_id,
            filename=doc.filename,
            file_size_bytes=doc.file_size_bytes,
            page_count=doc.page_count,
            chunk_count=len(chunks),
            status=DocumentStatus.READY,
            created_at=doc.created_at.isoformat(),
            chunks=chunks,
        )

    def delete_document(self, document_id: str) -> Optional[DocumentDeleteResponse]:
        """Deletes a document from disk, vector store, and storage registry."""
        if document_id not in self._documents:
            return None

        doc = self._documents.pop(document_id)
        chunks = self._chunks.pop(document_id, [])

        # Remove from vector store
        self.vector_store.delete_document(document_id)

        # Remove file from disk
        safe_filename = f"{document_id}_{Path(doc.filename).name}"
        file_path = self.upload_dir / safe_filename
        if file_path.exists():
            file_path.unlink()

        return DocumentDeleteResponse(
            success=True,
            message=(
                f"Document '{doc.filename}' and {len(chunks)} chunks "
                "deleted successfully."
            ),
        )


# Global singleton instance for API usage
document_service = DocumentService()
