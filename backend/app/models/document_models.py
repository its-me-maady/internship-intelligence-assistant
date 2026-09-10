from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class PageContent(BaseModel):
    """Represents text extracted from a specific page or section."""

    page_number: Optional[int] = Field(
        default=None,
        description="Physical 1-indexed page number for PDFs, or None for text.",
    )
    text: str = Field(description="Sanitized text content extracted from this page.")


class ParsedDocument(BaseModel):
    """In-memory representation of an ingested and parsed document."""

    document_id: str
    filename: str
    file_size_bytes: int
    pages: List[PageContent]
    raw_text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def page_count(self) -> int:
        return len(self.pages)


class DocumentChunk(BaseModel):
    """Enriched chunk with spatial and structural metadata."""

    chunk_id: str
    document_id: str
    filename: str
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    character_start: int
    character_end: int
    total_chunks: int
    uploaded_at: str


class DocumentUploadResponse(BaseModel):
    """Response returned upon successful document upload and chunking."""

    document_id: str
    filename: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    status: DocumentStatus = DocumentStatus.READY
    created_at: str


class DocumentSummary(BaseModel):
    """Summary record for document listing."""

    document_id: str
    filename: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    status: DocumentStatus
    created_at: str


class DocumentDetailResponse(BaseModel):
    """Full detail of an ingested document and its indexed chunks."""

    document_id: str
    filename: str
    file_size_bytes: int
    page_count: int
    chunk_count: int
    status: DocumentStatus
    created_at: str
    chunks: List[DocumentChunk]


class DocumentDeleteResponse(BaseModel):
    """Response returned after deleting a document."""

    success: bool
    message: str
