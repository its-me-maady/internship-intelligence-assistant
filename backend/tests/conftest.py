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

    def with_structured_output(self, schema, **kwargs):
        class StructuredOutputRunnable:
            def __init__(self, target_schema):
                self.target_schema = target_schema

            def invoke(self, input_messages, **run_kwargs):
                fields = getattr(self.target_schema, "model_fields", {})
                data = {}
                if "job_title" in fields:
                    data["job_title"] = "Machine Learning Research Intern"
                if "company_name" in fields:
                    data["company_name"] = "Neural Systems Inc."
                if "location" in fields:
                    data["location"] = "Mountain View, CA / Hybrid"
                if "work_type" in fields:
                    data["work_type"] = "Hybrid"
                if "stipend_or_salary" in fields:
                    data["stipend_or_salary"] = "$60 / hour"
                if "duration_weeks" in fields:
                    data["duration_weeks"] = 12
                if "application_deadline" in fields:
                    data["application_deadline"] = "November 15, 2026"
                if "required_technical_skills" in fields:
                    data["required_technical_skills"] = [
                        "Python",
                        "PyTorch",
                        "Transformers",
                    ]
                if "preferred_technical_skills" in fields:
                    data["preferred_technical_skills"] = ["CUDA", "Triton", "Ray"]
                if "required_soft_skills" in fields:
                    data["required_soft_skills"] = ["Team communication"]
                if "minimum_education" in fields:
                    data["minimum_education"] = "Pursuing MS/PhD in STEM"
                if "expected_graduation_years" in fields:
                    data["expected_graduation_years"] = ["2026", "2027"]
                if "minimum_gpa" in fields:
                    data["minimum_gpa"] = "3.0"
                if "prior_experience_required" in fields:
                    data["prior_experience_required"] = "Research experience"
                if "key_responsibilities" in fields:
                    data["key_responsibilities"] = ["Conduct deep learning evaluations"]
                if "raw_summary" in fields:
                    data["raw_summary"] = (
                        "12-week ML research internship on foundation models."
                    )
                return self.target_schema(**data)

        return StructuredOutputRunnable(schema)

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
