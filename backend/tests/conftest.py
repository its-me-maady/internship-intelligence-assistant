import hashlib
from typing import Any, List

import pytest
from app.services.document_service import document_service
from app.services.vector_service import ChromaVectorStore, EmbeddingService
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class FakeEmbeddingService(EmbeddingService):
    """Deterministic, offline embedding implementation for unit/integration testing."""

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


class FakeChatModel(BaseChatModel):
    """Deterministic, offline Fake Chat Model for testing."""

    response_text: str = (
        "According to [Source: doc.pdf, Page: 1], the requirements are verified."
    )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Any = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt_content = "\n".join(str(m.content) for m in messages)
        if (
            "favorite food" in prompt_content.lower()
            or "ceo salary" in prompt_content.lower()
        ):
            content = (
                "I cannot find sufficient information in the uploaded "
                "internship document(s) to answer this question accurately."
            )
        else:
            content = self.response_text
        generation = ChatGeneration(message=AIMessage(content=content))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "fake-chat-model"


@pytest.fixture
def fake_embedding_service() -> FakeEmbeddingService:
    return FakeEmbeddingService(dimension=16)


@pytest.fixture
def fake_chat_model() -> FakeChatModel:
    return FakeChatModel()


@pytest.fixture(autouse=True)
def mock_vector_store(tmp_path, monkeypatch):
    """Autouse fixture providing an isolated, offline ChromaVectorStore.

    Applies to all tests across the backend test suite.
    """
    test_chroma_dir = str(tmp_path / "global_test_chroma")
    fake_store = ChromaVectorStore(
        persist_directory=test_chroma_dir,
        collection_name="test_internship_documents",
        embedding_service=FakeEmbeddingService(dimension=16),
    )

    monkeypatch.setattr("app.main.get_vector_store", lambda: fake_store)
    monkeypatch.setattr(
        "app.services.document_service.get_vector_store", lambda: fake_store
    )
    monkeypatch.setattr(
        "app.services.vector_service.get_vector_store", lambda: fake_store
    )
    monkeypatch.setattr(document_service, "_vector_store", fake_store)
    monkeypatch.setattr(document_service, "_documents", {})
    monkeypatch.setattr(document_service, "_chunks", {})

    return fake_store


@pytest.fixture(autouse=True)
def mock_llm_service(monkeypatch):
    """Autouse fixture providing an offline FakeChatModel for all tests."""
    fake_llm = FakeChatModel()
    monkeypatch.setattr("app.services.llm_service.get_llm", lambda: fake_llm)
    return fake_llm
