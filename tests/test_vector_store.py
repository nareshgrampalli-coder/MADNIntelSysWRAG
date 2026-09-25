from datetime import datetime, timedelta, timezone

import pytest

from news_rag.models import ArticleChunk, NewsCategory
from news_rag.vector_store import HashEmbeddingProvider, JsonVectorStore


def chunk(chunk_id: str, category: NewsCategory, days_ago: int = 0) -> ArticleChunk:
    return ArticleChunk(
        chunk_id=chunk_id,
        article_url=f"https://example.com/{chunk_id}",
        text="RBI policy rate and finance markets",
        chunk_index=0,
        category=category,
        source="Example News",
        published_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        metadata={"title": "Policy update"},
    )


def test_hash_embeddings_are_deterministic_and_normalized() -> None:
    provider = HashEmbeddingProvider(dimensions=8)

    first = provider.embed("RBI policy")
    second = provider.embed("RBI policy")

    assert first == second
    assert sum(value * value for value in first) == pytest.approx(1.0)


def test_json_store_upsert_is_idempotent_and_persists(tmp_path) -> None:
    path = tmp_path / "vectors.json"
    store = JsonVectorStore(path)
    article = chunk("one", NewsCategory.FINANCE)

    store.upsert([article, article])
    restored = JsonVectorStore(path)

    assert store.count() == 1
    assert restored.count() == 1
    assert restored.query("policy", category=NewsCategory.FINANCE)[0].article_url == article.article_url


def test_json_store_filters_category_and_date(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert([chunk("finance", NewsCategory.FINANCE), chunk("tech", NewsCategory.TECHNOLOGY, days_ago=10)])
    cutoff = datetime.now(timezone.utc) - timedelta(days=2)

    results = store.query("policy", category=NewsCategory.FINANCE, published_after=cutoff)

    assert [result.chunk_id for result in results] == ["finance"]


def test_json_store_reset_removes_all_records(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert([chunk("one", NewsCategory.FINANCE)])

    store.reset()

    assert store.count() == 0
