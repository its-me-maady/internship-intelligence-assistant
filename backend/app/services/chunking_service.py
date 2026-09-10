import uuid
from typing import List

from app.models.document_models import DocumentChunk, ParsedDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChunkingService:
    """Service for splitting parsed documents into enriched semantic chunks."""

    DEFAULT_CHUNK_SIZE = 800
    DEFAULT_CHUNK_OVERLAP = 150
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        separators: List[str] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            keep_separator=True,
        )

    def split_document(self, document: ParsedDocument) -> List[DocumentChunk]:
        """Splits a ParsedDocument into an ordered list of DocumentChunk objects."""
        if not document.raw_text.strip():
            return []

        uploaded_at_str = document.created_at.isoformat()
        chunks: List[DocumentChunk] = []
        global_char_offset = 0

        for page in document.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            # Split text for this specific page/section
            raw_splits = self.splitter.split_text(page_text)

            page_char_offset = 0
            for split_content in raw_splits:
                # Find start coordinate in page_text
                start_pos = page_text.find(split_content, page_char_offset)
                if start_pos == -1:
                    start_pos = page_char_offset

                char_start = global_char_offset + start_pos
                char_end = char_start + len(split_content)

                chunk = DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document.document_id,
                    filename=document.filename,
                    content=split_content,
                    chunk_index=len(chunks),
                    page_number=page.page_number,
                    character_start=char_start,
                    character_end=char_end,
                    total_chunks=0,  # Updated after all chunks are created
                    uploaded_at=uploaded_at_str,
                )
                chunks.append(chunk)
                page_char_offset = start_pos + max(
                    1, len(split_content) - self.chunk_overlap
                )

            global_char_offset += len(page_text) + 2  # account for paragraph spacing

        # Update total_chunks for all generated chunks
        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total

        return chunks
