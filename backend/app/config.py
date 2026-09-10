from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Metadata
    APP_NAME: str = "Internship Intelligence Assistant"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # AI & Embeddings
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_MODEL: str = "models/text-embedding-004"

    # Storage & ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = str(
        Path(__file__).resolve().parent.parent.parent / "data" / "chroma"
    )
    UPLOAD_DIRECTORY: str = str(
        Path(__file__).resolve().parent.parent.parent / "data" / "uploads"
    )
    MAX_FILE_SIZE_MB: int = 15


settings = Settings()
