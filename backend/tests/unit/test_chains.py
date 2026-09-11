from typing import Any, List
from unittest.mock import MagicMock

import pytest
from app.models.chat_models import ChatMessage
from app.rag.chains import RAGChain
from app.rag.prompts import STANDARD_REFUSAL_MESSAGE
from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class MockChatModel(BaseChatModel):
    """Deterministic Mock Chat Model for unit tests."""

    response_text: str = (
        "According to [Source: alpha.pdf, Page: 1], Python 3.12 is required."
    )
    recorded_messages: List[BaseMessage] = []

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Any = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.recorded_messages = messages
        generation = ChatGeneration(message=AIMessage(content=self.response_text))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "mock-chat-model"


class TestRAGChain:
    """Unit tests for RAGChain context formatting, grounding, and refusal guardrails."""

    @pytest.fixture
    def mock_retriever(self):
        retriever = MagicMock()
        retriever.retrieve.return_value = [
            Document(
                page_content="Python 3.12 and FastAPI are required qualifications.",
                metadata={
                    "document_id": "doc-123",
                    "filename": "alpha.pdf",
                    "page_number": 1,
                    "chunk_index": 0,
                    "chunk_id": "c1",
                },
            )
        ]
        return retriever

    def test_chain_generates_grounded_answer_with_sources(self, mock_retriever):
        mock_llm = MockChatModel(
            response_text="The role requires Python 3.12 [Source: alpha.pdf, Page: 1]."
        )
        chain = RAGChain(retriever=mock_retriever, llm=mock_llm)

        response = chain.invoke(query="What skills are required?")

        assert response.is_grounded is True
        assert "Python 3.12" in response.answer
        assert len(response.sources) == 1
        assert response.sources[0].document_id == "doc-123"
        assert response.sources[0].filename == "alpha.pdf"
        assert response.sources[0].page_number == 1
        assert response.sources[0].chunk_index == 0
        assert "FastAPI" in response.sources[0].snippet

    def test_chain_zero_matching_chunks_triggers_refusal_without_calling_llm(self):
        empty_retriever = MagicMock()
        empty_retriever.retrieve.return_value = []

        mock_llm = MagicMock()
        chain = RAGChain(retriever=empty_retriever, llm=mock_llm)

        response = chain.invoke(query="What is the compensation?")

        # LLM should not be called at all
        mock_llm.invoke.assert_not_called()
        mock_llm.generate.assert_not_called()

        assert response.is_grounded is False
        assert response.answer == STANDARD_REFUSAL_MESSAGE
        assert response.sources == []

    def test_chain_preserves_conversation_history(self, mock_retriever):
        mock_llm = MockChatModel(response_text="Yes, that is correct.")
        chain = RAGChain(retriever=mock_retriever, llm=mock_llm)

        history = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="How can I help you?"),
        ]

        response = chain.invoke(
            query="Tell me about FastAPI requirements",
            chat_history=history,
        )

        assert response.is_grounded is True
        # Verify history was included in recorded messages
        history_contents = [m.content for m in mock_llm.recorded_messages]
        assert "Hello" in history_contents
        assert "How can I help you?" in history_contents

    def test_chain_detects_llm_refusal_and_sets_is_grounded_false(self, mock_retriever):
        mock_llm = MockChatModel(response_text=STANDARD_REFUSAL_MESSAGE)
        chain = RAGChain(retriever=mock_retriever, llm=mock_llm)

        response = chain.invoke(query="What is the CEO salary?")

        assert response.is_grounded is False
        assert STANDARD_REFUSAL_MESSAGE in response.answer
