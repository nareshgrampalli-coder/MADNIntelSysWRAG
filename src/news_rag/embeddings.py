"""Embedding provider interfaces and implementations."""

from functools import lru_cache
from importlib import import_module
import hashlib
import math
from typing import Protocol


class EmbeddingProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    def embed(self, text: str) -> list[float]: ...

    def embed_many(self, texts: list[str]) -> list[list[float]]: ...


EMBEDDING_FALLBACK_MESSAGE = (
    "sentence-transformers is unavailable, so the app is using HashEmbeddingProvider. "
    'Install or repair it with `py -m pip install -e ".[embeddings]"` to enable semantic embeddings.'
)


class EmbeddingDependencyMissing(RuntimeError):
    pass


class EmbeddingProviderMismatch(RuntimeError):
    pass


class HashEmbeddingProvider:
    """Deterministic local embeddings for development and tests."""

    def __init__(self, dimensions: int = 32) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    @property
    def provider_id(self) -> str:
        return f"hash:{self.dimensions}"

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in text.casefold().split():
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0
        magnitude = math.sqrt(sum(value * value for value in vector))
        return [value / magnitude for value in vector] if magnitude else vector

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


class SentenceTransformerEmbeddingProvider:
    """Optional local sentence-transformers embeddings."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        try:
            import_module("sentence_transformers")
        except ImportError as error:
            detail = f" Import error: {error}"
            raise EmbeddingDependencyMissing(EMBEDDING_FALLBACK_MESSAGE + detail) from error
        self.model = None

    @property
    def provider_id(self) -> str:
        return f"sentence-transformers:{self.model_name}"

    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.model is None:
            self.model = _load_sentence_transformer(self.model_name)
        vectors = self.model.encode(texts, normalize_embeddings=True)
        if hasattr(vectors, "tolist"):
            vectors = vectors.tolist()
        return [[float(value) for value in vector] for vector in vectors]


@lru_cache(maxsize=2)
def _load_sentence_transformer(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as error:
        detail = f" Import error: {error}"
        raise EmbeddingDependencyMissing(EMBEDDING_FALLBACK_MESSAGE + detail) from error
    return SentenceTransformer(model_name)