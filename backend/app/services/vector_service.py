from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from app.config import settings
from app.models.document_models import DocumentChunk
from fastembed import TextEmbedding
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings


class EmbeddingService(Embeddings, ABC):
    """Abstract base class for modular embedding providers."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass


class LocalMiniLMEmbeddingService(EmbeddingService):
    """Local, CPU-optimized ONNX embedding service using FastEmbed."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model: Optional[TextEmbedding] = None

    @property
    def model(self) -> TextEmbedding:
        if self._model is None:
            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]

    def embed_query(self, text: str) -> List[float]:
        if not text:
            return []
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()


class GeminiEmbeddingService(EmbeddingService):
    """Google Gemini AI embedding service."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "models/text-embedding-004",
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self._client = GoogleGenerativeAIEmbeddings(
            model=self.model,
            google_api_key=self.api_key,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._client.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._client.embed_query(text)


class EmbeddingServiceFactory:
    """Factory to instantiate the appropriate EmbeddingService."""

    @staticmethod
    def get_embedding_service(
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> EmbeddingService:
        prov = (provider or settings.EMBEDDING_PROVIDER).lower().strip()
        if prov == "gemini":
            return GeminiEmbeddingService(api_key=api_key)
        elif prov in {"local", "minilm"}:
            return LocalMiniLMEmbeddingService()
        else:
            raise ValueError(
                f"Unsupported embedding provider '{prov}'. Supported: 'gemini', 'local'"
            )


class ChromaVectorStore:
    """Persistent vector store wrapper for ChromaDB."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.persist_dir = Path(persist_directory or settings.CHROMA_PERSIST_DIRECTORY)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME

        self.embedding_service = (
            embedding_service or EmbeddingServiceFactory.get_embedding_service()
        )

        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Internship document embeddings"},
        )

        self.vector_store = Chroma(
            client=self._client,
            collection_name=self.collection_name,
            embedding_function=self.embedding_service,
        )

    def add_chunks(self, chunks: List[DocumentChunk]) -> List[str]:
        """Indexes an array of DocumentChunk objects into ChromaDB."""
        if not chunks:
            return []

        documents: List[Document] = []
        ids: List[str] = []

        for chunk in chunks:
            page_num = chunk.page_number if chunk.page_number is not None else -1
            metadata: Dict[str, Any] = {
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "page_number": page_num,
                "character_start": chunk.character_start,
                "character_end": chunk.character_end,
                "total_chunks": chunk.total_chunks,
                "uploaded_at": chunk.uploaded_at,
            }
            documents.append(Document(page_content=chunk.content, metadata=metadata))
            ids.append(chunk.chunk_id)

        self.vector_store.add_documents(documents=documents, ids=ids)
        return ids

    def delete_document(self, document_id: str) -> int:
        """Deletes all chunks matching document_id from ChromaDB."""
        results = self._collection.get(where={"document_id": document_id})
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            self._collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Searches for Top-K most similar chunks to query."""
        return self.vector_store.similarity_search(query=query, k=k, filter=filter)

    def get_total_chunks_count(self) -> int:
        """Returns the total number of chunks stored in ChromaDB."""
        return self._collection.count()

    def get_indexed_documents_count(self) -> int:
        """Returns the total count of distinct documents indexed in ChromaDB."""
        all_metadata = self._collection.get(include=["metadatas"])
        metadatas = all_metadata.get("metadatas") or []
        doc_ids = {m["document_id"] for m in metadatas if m and "document_id" in m}
        return len(doc_ids)


@lru_cache
def get_vector_store() -> ChromaVectorStore:
    """Returns a cached, lazily-initialized ChromaVectorStore instance."""
    return ChromaVectorStore()
