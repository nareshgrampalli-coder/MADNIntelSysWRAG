"""Embedding and vector-store boundaries for article chunks."""

from collections.abc import Iterable, Sequence
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import hashlib
import math
import re

from .models import ArticleChunk, NewsCategory


class HashEmbeddingProvider:
    """Deterministic local embeddings for development and tests."""

    def __init__(self, dimensions: int = 32) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in text.casefold().split():
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0
        magnitude = math.sqrt(sum(value * value for value in vector))
        return [value / magnitude for value in vector] if magnitude else vector


class JsonVectorStore:
    """Small persistent vector store used for local development and tests."""

    def __init__(self, path: Path, embedding_provider: HashEmbeddingProvider | None = None) -> None:
        self.path = path
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()
        self._records: dict[str, dict[str, object]] = {}
        self._load()

    def upsert(self, chunks: Iterable[ArticleChunk]) -> None:
        for chunk in chunks:
            self._records[chunk.chunk_id] = {
                "id": chunk.chunk_id,
                "text": chunk.text,
                "embedding": self.embedding_provider.embed(chunk.text),
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
            lexical_score = _lexical_overlap(text, record["text"])
            score = 0.7 * semantic_score + 0.3 * lexical_score
            candidates.append((score, _record_to_chunk(record)))
        candidates.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in candidates[: max(0, limit)]]

    def count(self) -> int:
        return len(self._records)

    def reset(self) -> None:
        self._records.clear()
        self._save()

    def _load(self) -> None:
        if self.path.exists():
            self._records = json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._records, indent=2), encoding="utf-8")


class ChromaVectorStore:
    """Optional ChromaDB adapter with the same upsert/query contract."""

    def __init__(self, path: Path, collection_name: str = "news_chunks") -> None:
        try:
            import chromadb
        except ImportError as error:
            raise RuntimeError("Install the 'vector' extra to use ChromaDB") from error
        client = chromadb.PersistentClient(path=str(path))
        self.collection = client.get_or_create_collection(collection_name)

    def upsert(self, chunks: Iterable[ArticleChunk]) -> None:
        chunks = list(chunks)
        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[_chunk_metadata(chunk) for chunk in chunks],
        )

    def count(self) -> int:
        return self.collection.count()

    def reset(self) -> None:
        self.collection.delete(where={})


def _chunk_metadata(chunk: ArticleChunk) -> dict[str, str]:
    return {
        "category": chunk.category.value,
        "source": chunk.source,
        "article_url": chunk.article_url,
        "published_at": chunk.published_at.isoformat(),
        **chunk.metadata,
    }


def _record_to_chunk(record: dict[str, object]) -> ArticleChunk:
    metadata = record["metadata"]
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
