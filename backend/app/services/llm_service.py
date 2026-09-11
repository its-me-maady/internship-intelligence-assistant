from functools import lru_cache
from typing import Optional

from app.config import settings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI


class LLMServiceFactory:
    """Factory to instantiate the appropriate ChatModel."""

    @staticmethod
    def get_chat_model(
        provider: str = "gemini",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
    ) -> BaseChatModel:
        prov = provider.lower().strip()
        if prov == "gemini":
            key = api_key or settings.GEMINI_API_KEY
            model_name = model or settings.LLM_MODEL
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=key,
                temperature=temperature,
            )
        else:
            raise ValueError(
                f"Unsupported LLM provider '{provider}'. Supported: 'gemini'"
            )


@lru_cache
def get_llm() -> BaseChatModel:
    """Returns a cached, lazily-initialized LLM chat model instance."""
    return LLMServiceFactory.get_chat_model()
