from datetime import datetime, timedelta, timezone
import sys
from types import ModuleType

import pytest

from news_rag.models import ArticleChunk, NewsCategory
from news_rag.config import Settings
from news_rag.vector_store import (
    EMBEDDING_FALLBACK_MESSAGE,
    HashEmbeddingProvider,
    JsonVectorStore,
    SentenceTransformerEmbeddingProvider,
    _load_sentence_transformer,
    build_vector_store,
)


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


def test_json_store_evicts_records_older_than_max_age(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json", max_age_days=14)
    store.upsert([chunk("stale", NewsCategory.FINANCE, days_ago=30)])

    store.upsert([chunk("fresh", NewsCategory.FINANCE)])

    assert store.count() == 1
    assert [result.chunk_id for result in store.query("policy", limit=5)] == ["fresh"]


def test_vector_store_factory_defaults_to_json(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("NEWS_RAG_VECTOR_BACKEND", raising=False)
    monkeypatch.setenv("NEWS_RAG_EMBEDDING_PROVIDER", "hash")
    settings = Settings(vector_store_dir=tmp_path)

    store = build_vector_store(settings)

    assert isinstance(store, JsonVectorStore)


def test_vector_store_factory_defaults_to_sentence_transformers(tmp_path, monkeypatch) -> None:
    class FakeModel:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def encode(self, text: str, normalize_embeddings: bool):
            return [1.0, 0.0]

    fake_module = ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = FakeModel
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)
    monkeypatch.delenv("NEWS_RAG_VECTOR_BACKEND", raising=False)
    monkeypatch.delenv("NEWS_RAG_EMBEDDING_PROVIDER", raising=False)

    store = build_vector_store(Settings(vector_store_dir=tmp_path))

    assert store.embedding_provider.provider_id == (
        "sentence-transformers:sentence-transformers/all-MiniLM-L6-v2"
    )
    assert store.embedding_warning is None


def test_vector_store_falls_back_to_hash_with_clear_warning_when_package_missing(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    _load_sentence_transformer.cache_clear()
    monkeypatch.delenv("NEWS_RAG_VECTOR_BACKEND", raising=False)
    monkeypatch.delenv("NEWS_RAG_EMBEDDING_PROVIDER", raising=False)

    store = build_vector_store(Settings(vector_store_dir=tmp_path))

    assert isinstance(store.embedding_provider, HashEmbeddingProvider)
    assert store.embedding_warning.startswith(EMBEDDING_FALLBACK_MESSAGE)
    assert "Import error:" in store.embedding_warning


def test_vector_store_factory_rejects_unknown_backend(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("NEWS_RAG_VECTOR_BACKEND", "unknown")

    with pytest.raises(ValueError, match="json.*chroma"):
        build_vector_store(Settings(vector_store_dir=tmp_path))


def test_sentence_transformer_provider_normalizes_model_output(monkeypatch) -> None:
    class FakeModel:
        def __init__(self, model_name: str) -> None:
            assert model_name == "test/model"

        def encode(self, text: str, normalize_embeddings: bool):
            assert text == "news query"
            assert normalize_embeddings is True
            return [0.6, 0.8]

    fake_module = ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = FakeModel
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)

    provider = SentenceTransformerEmbeddingProvider("test/model")

    assert provider.provider_id == "sentence-transformers:test/model"
    assert provider.embed("news query") == [0.6, 0.8]


def test_vector_store_factory_uses_configured_sentence_transformer(tmp_path, monkeypatch) -> None:
    class FakeModel:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def encode(self, text: str, normalize_embeddings: bool):
            return [1.0, 0.0]

    fake_module = ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = FakeModel
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)
    monkeypatch.delenv("NEWS_RAG_VECTOR_BACKEND", raising=False)

    store = build_vector_store(
        Settings(
            vector_store_dir=tmp_path,
            embedding_provider="sentence-transformers",
            embedding_model="test/model",
        )
    )

    assert isinstance(store, JsonVectorStore)
    assert store.embedding_provider.provider_id == "sentence-transformers:test/model"


def test_json_store_requires_reindex_after_embedding_provider_change(tmp_path) -> None:
    path = tmp_path / "vectors.json"
    original = JsonVectorStore(path)
    original.upsert([chunk("finance", NewsCategory.FINANCE)])
    changed = JsonVectorStore(path, embedding_provider=HashEmbeddingProvider(dimensions=8))

    with pytest.raises(RuntimeError, match="reset and re-ingest"):
        changed.query("policy")

    changed.reset()
    changed.upsert([chunk("finance", NewsCategory.FINANCE)])

    assert changed.count() == 1
