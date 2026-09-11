from typing import List, Optional

from app.services import vector_service
from langchain_core.documents import Document


class DocumentRetriever:
    """Retrieves relevant document chunks from ChromaVectorStore."""

    def __init__(self, vector_store: Optional[vector_service.ChromaVectorStore] = None):
        self._vector_store = vector_store

    @property
    def vector_store(self) -> vector_service.ChromaVectorStore:
        if self._vector_store is not None:
            return self._vector_store
        return vector_service.get_vector_store()

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        document_id: Optional[str] = None,
    ) -> List[Document]:
        """Retrieves top_k most similar chunks, optionally filtered by document_id."""
        filter_dict = {"document_id": document_id} if document_id else None
        return self.vector_store.similarity_search(
            query=query,
            k=top_k,
            filter=filter_dict,
        )
