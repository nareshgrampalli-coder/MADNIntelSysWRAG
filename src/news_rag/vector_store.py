"""Embedding and vector-store boundaries for article chunks."""

from collections.abc import Iterable, Sequence
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import hashlib
import math
import re
from typing import Protocol

from .models import ArticleChunk, NewsCategory


class VectorStore(Protocol):
    def upsert(self, chunks: Iterable[ArticleChunk]) -> None: ...

    def query(
        self,
        text: str,
        category: NewsCategory | None = None,
        published_after: datetime | None = None,
        limit: int = 5,
    ) -> list[ArticleChunk]: ...

    def count(self) -> int: ...


class EmbeddingProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    def embed(self, text: str) -> list[float]: ...


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


class SentenceTransformerEmbeddingProvider:
    """Optional local sentence-transformers embeddings."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "Install the 'embeddings' extra to use sentence-transformers"
            ) from error
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    @property
    def provider_id(self) -> str:
        return f"sentence-transformers:{self.model_name}"

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True)
        if hasattr(vector, "tolist"):
            vector = vector.tolist()
        return [float(value) for value in vector]


class JsonVectorStore:
    """Small persistent vector store used for local development and tests."""

    def __init__(
        self,
        path: Path,
        embedding_provider: EmbeddingProvider | None = None,
        max_age_days: int = 14,
    ) -> None:
        self.path = path
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()
        self.max_age_days = max(1, max_age_days)
        self._records: dict[str, dict[str, object]] = {}
        self._load()

    def upsert(self, chunks: Iterable[ArticleChunk]) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)
        self._records = {
            key: record
            for key, record in self._records.items()
            if _record_published_at(record) >= cutoff
        }
        self._validate_embedding_compatibility()
        for chunk in chunks:
            self._records[chunk.chunk_id] = {
                "id": chunk.chunk_id,
                "text": chunk.text,
                "embedding": self.embedding_provider.embed(_chunk_search_text(chunk)),
                "embedding_provider": self.embedding_provider.provider_id,
                "metadata": _chunk_metadata(chunk),
            }
        self._save()

    def query(
        self,
        text: str,
        category: NewsCategory | None = None,
        published_after: datetime | None = None,
        limit: int = 5,
    ) -> list[ArticleChunk]:
        self._validate_embedding_compatibility()
        query_embedding = self.embedding_provider.embed(text)
        candidates = []
        for record in self._records.values():
            metadata = record["metadata"]
            if category and metadata["category"] != category.value:
                continue
            published_at = datetime.fromisoformat(metadata["published_at"])
            if published_after and published_at < published_after:
                continue
            semantic_score = _cosine_similarity(query_embedding, record["embedding"])
            lexical_score = _lexical_overlap(text, _record_search_text(record))
            score = 0.7 * semantic_score + 0.3 * lexical_score
            candidates.append((score, _record_to_chunk(record)))
        candidates.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in candidates[: max(0, limit)]]

    def count(self) -> int:
        return len(self._records)

    def reset(self) -> None:
        self._records.clear()
        self._save()

    def _validate_embedding_compatibility(self) -> None:
        incompatible = {
            record.get("embedding_provider", "hash:32")
            for record in self._records.values()
            if record.get("embedding_provider", "hash:32") != self.embedding_provider.provider_id
        }
        if incompatible:
            raise RuntimeError(
                "Stored vectors use a different embedding provider; reset and re-ingest "
                f"the index before using {self.embedding_provider.provider_id}."
            )

    def _load(self) -> None:
        if self.path.exists():
            self._records = json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._records, indent=2), encoding="utf-8")


class ChromaVectorStore:
    """Optional ChromaDB adapter with the same upsert/query contract."""

    def __init__(
        self,
        path: Path,
        collection_name: str = "news_chunks",
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        try:
            import chromadb
        except ImportError as error:
            raise RuntimeError("Install the 'vector' extra to use ChromaDB") from error
        client = chromadb.PersistentClient(path=str(path))
        self.collection = client.get_or_create_collection(collection_name)
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()

    def upsert(self, chunks: Iterable[ArticleChunk]) -> None:
        chunks = list(chunks)
        self._validate_embedding_compatibility()
        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=[self.embedding_provider.embed(_chunk_search_text(chunk)) for chunk in chunks],
            metadatas=[
                {**_chunk_metadata(chunk), "_embedding_provider": self.embedding_provider.provider_id}
                for chunk in chunks
            ],
        )

    def query(
        self,
        text: str,
        category: NewsCategory | None = None,
        published_after: datetime | None = None,
        limit: int = 5,
    ) -> list[ArticleChunk]:
        if limit <= 0:
            return []
        self._validate_embedding_compatibility()
        filters = []
        if category:
            filters.append({"category": category.value})
        if published_after:
            filters.append({"published_at": {"$gte": published_after.isoformat()}})
        kwargs: dict[str, object] = {
            "query_embeddings": [self.embedding_provider.embed(text)],
            "n_results": limit,
        }
        if filters:
            kwargs["where"] = filters[0] if len(filters) == 1 else {"$and": filters}
        results = self.collection.query(**kwargs)
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        return [
            _record_to_chunk({"id": record_id, "text": document, "metadata": metadata})
            for record_id, document, metadata in zip(ids, documents, metadatas, strict=True)
        ]

    def count(self) -> int:
        return self.collection.count()

    def reset(self) -> None:
        self.collection.delete(where={})

    def _validate_embedding_compatibility(self) -> None:
        records = self.collection.get(limit=1, include=["metadatas"])
        metadatas = records.get("metadatas", [])
        if not metadatas:
            return
        provider_id = metadatas[0].get("_embedding_provider", "chromadb-default")
        if provider_id != self.embedding_provider.provider_id:
            raise RuntimeError(
                "Stored vectors use a different embedding provider; reset and re-ingest "
                f"the index before using {self.embedding_provider.provider_id}."
            )


def build_vector_store(settings: object) -> VectorStore:
    """Build the configured backend, defaulting to the local JSON store."""
    backend = os.getenv("NEWS_RAG_VECTOR_BACKEND", "json").casefold()
    path = settings.vector_store_dir
    embedding_provider = _build_embedding_provider(
        getattr(settings, "embedding_provider", None) or os.getenv("NEWS_RAG_EMBEDDING_PROVIDER", "hash"),
        getattr(settings, "embedding_model", None) or os.getenv("NEWS_RAG_EMBEDDING_MODEL", ""),
    )
    if backend == "chroma":
        return ChromaVectorStore(path, embedding_provider=embedding_provider)
    if backend == "json":
        max_age_days = int(os.getenv("NEWS_RAG_MAX_AGE_DAYS", "14"))
        return JsonVectorStore(
            path / "vectors.json",
            embedding_provider=embedding_provider,
            max_age_days=max_age_days,
        )
    raise ValueError("NEWS_RAG_VECTOR_BACKEND must be 'json' or 'chroma'")


def _build_embedding_provider(provider_name: str, model_name: str) -> EmbeddingProvider:
    normalized = provider_name.casefold().replace("_", "-")
    if normalized == "hash":
        return HashEmbeddingProvider()
    if normalized in {"sentence-transformers", "sentence-transformer"}:
        return SentenceTransformerEmbeddingProvider(
            model_name or "sentence-transformers/all-MiniLM-L6-v2"
        )
    raise ValueError(
        "NEWS_RAG_EMBEDDING_PROVIDER must be 'hash' or 'sentence-transformers'"
    )


def _record_published_at(record: dict[str, object]) -> datetime:
    try:
        return datetime.fromisoformat(record["metadata"]["published_at"])
    except (KeyError, TypeError, ValueError):
        return datetime.now(timezone.utc)


def _chunk_metadata(chunk: ArticleChunk) -> dict[str, str]:
    return {
        "category": chunk.category.value,
        "source": chunk.source,
        "article_url": chunk.article_url,
        "published_at": chunk.published_at.isoformat(),
        **chunk.metadata,
    }


def _chunk_search_text(chunk: ArticleChunk) -> str:
    return f"{chunk.metadata.get('title', '')} {chunk.text}"


def _record_search_text(record: dict[str, object]) -> str:
    metadata = record["metadata"]
    title = metadata.get("title", "") if isinstance(metadata, dict) else ""
    return f"{title} {record['text']}"


def _record_to_chunk(record: dict[str, object]) -> ArticleChunk:
    metadata = record["metadata"]
    metadata = {key: value for key, value in metadata.items() if key != "_embedding_provider"}
    return ArticleChunk(
        chunk_id=record["id"],
        article_url=metadata["article_url"],
        text=record["text"],
        chunk_index=int(metadata.get("chunk_index", "0")),
        category=NewsCategory(metadata["category"]),
        source=metadata["source"],
        published_at=datetime.fromisoformat(metadata["published_at"]),
        metadata=metadata,
    )


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _lexical_overlap(query: str, document: str) -> float:
    query_terms = set(re.findall(r"[a-z0-9]+", query.casefold()))
    document_terms = set(re.findall(r"[a-z0-9]+", document.casefold()))
    if not query_terms:
        return 0.0
    return len(query_terms & document_terms) / len(query_terms)
