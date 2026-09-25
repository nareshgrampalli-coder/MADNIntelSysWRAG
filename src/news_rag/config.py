"""Environment-backed application configuration."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    log_level: str = "INFO"
    data_dir: Path = Path("data")
    vector_store_dir: Path = Path("data/chroma")
    llm_provider: str | None = None
    llm_model: str | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            environment=os.getenv("NEWS_RAG_ENV", "development"),
            log_level=os.getenv("NEWS_RAG_LOG_LEVEL", "INFO"),
            data_dir=Path(os.getenv("NEWS_RAG_DATA_DIR", "data")),
            vector_store_dir=Path(os.getenv("NEWS_RAG_VECTOR_STORE_DIR", "data/chroma")),
            llm_provider=os.getenv("NEWS_RAG_LLM_PROVIDER") or None,
            llm_model=os.getenv("NEWS_RAG_LLM_MODEL") or None,
            embedding_provider=os.getenv("NEWS_RAG_EMBEDDING_PROVIDER") or None,
            embedding_model=os.getenv("NEWS_RAG_EMBEDDING_MODEL") or None,
        )
