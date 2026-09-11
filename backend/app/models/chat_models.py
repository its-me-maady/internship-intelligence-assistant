from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Represents a single message in a conversation turn."""

    role: str = Field(
        ...,
        description="Role of the speaker (e.g. 'user', 'assistant', 'system').",
    )
    content: str = Field(..., description="Message text content.")


class ChatRequest(BaseModel):
    """Request payload for grounded RAG conversational query."""

    query: str = Field(
        ...,
        min_length=1,
        description="User's natural language question regarding the internship.",
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Optional document ID filter to isolate search to one document.",
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=20,
        description="Number of most relevant chunks to retrieve from vector store.",
    )
    chat_history: Optional[List[ChatMessage]] = Field(
        default_factory=list,
        description="Prior conversation history for context preservation.",
    )


class ChatSourceChunk(BaseModel):
    """Source citation metadata attached to the response."""

    document_id: str = Field(..., description="Unique ID of source document.")
    filename: str = Field(..., description="Original filename of source document.")
    page_number: Optional[int] = Field(
        default=None,
        description="1-based page number where chunk appears (for multi-page docs).",
    )
    chunk_index: int = Field(
        ..., description="0-based index of the chunk in the document sequence."
    )
    snippet: str = Field(
        ..., description="Excerpt snippet of the chunk used for grounding."
    )


class ChatResponse(BaseModel):
    """Response payload for grounded conversational query."""

    answer: str = Field(
        ...,
        description="Factual, grounded answer or polite refusal from the assistant.",
    )
    is_grounded: bool = Field(
        ...,
        description="True if answered from retrieved context; False if refused.",
    )
    sources: List[ChatSourceChunk] = Field(
        default_factory=list,
        description="List of cited source chunks used to generate the answer.",
    )
