from datetime import datetime, timedelta, timezone

from news_rag.models import ArticleChunk, NewsCategory
from news_rag.query_engine import QueryEngine, QueryInterpreter
from news_rag.vector_store import JsonVectorStore


def make_chunk(chunk_id: str, category: NewsCategory, days_ago: int, text: str) -> ArticleChunk:
    return ArticleChunk(
        chunk_id=chunk_id,
        article_url=f"https://example.com/{chunk_id}",
        text=text,
        chunk_index=0,
        category=category,
        source="Example News",
        published_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        metadata={"title": f"{category.value} story"},
    )


def test_query_interpreter_extracts_category_and_relative_date() -> None:
    now = datetime(2026, 9, 26, tzinfo=timezone.utc)
    filters = QueryInterpreter(clock=lambda: now).interpret("What happened in finance this week?")

    assert filters.category is NewsCategory.FINANCE
    assert filters.published_after == now - timedelta(days=7)


def test_query_engine_returns_grounded_answer_and_unique_citations(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    first = make_chunk("one", NewsCategory.FINANCE, 0, "RBI announced a policy rate change")
    second = make_chunk("two", NewsCategory.FINANCE, 1, "Markets reacted to the RBI announcement")
    store.upsert([first, second])

    response = QueryEngine(store).answer("What happened in finance?")

    assert response.grounded is True
    assert "RBI" in response.answer
    assert len(response.citations) == 2
    assert response.citations[0].url.startswith("https://")


def test_query_engine_refuses_when_filters_find_no_evidence(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert([make_chunk("old", NewsCategory.TECHNOLOGY, 30, "Old technology story")])

    response = QueryEngine(store, interpreter=QueryInterpreter(clock=lambda: datetime(2026, 9, 26, tzinfo=timezone.utc))).answer(
        "What happened in finance this week?"
    )

    assert response.grounded is False
    assert response.citations == ()
    assert response.answer == "I don't have news on that."


def test_query_engine_supports_explicit_dates(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert([make_chunk("new", NewsCategory.POLITICS, 0, "Politics update")])
    interpreter = QueryInterpreter(clock=lambda: datetime(2026, 9, 26, tzinfo=timezone.utc))

    response = QueryEngine(store, interpreter=interpreter).answer("Politics news since 2026-09-25")

    assert response.grounded is True


def test_query_engine_reranks_relevant_evidence_before_recency(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    recent_broad = make_chunk("recent", NewsCategory.FINANCE, 0, "Markets had a quiet trading session")
    older_relevant = make_chunk("relevant", NewsCategory.FINANCE, 2, "RBI announced a policy rate change")
    store.upsert([recent_broad, older_relevant])

    response = QueryEngine(store).answer("What did the RBI announce?")

    assert response.citations[0].url.endswith("/relevant")


def test_query_engine_prioritizes_support_and_resistance_evidence(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert(
        [
            make_chunk("decline", NewsCategory.STOCKS, 0, "SENSEX and Nifty declined today"),
            make_chunk("support", NewsCategory.STOCKS, 1, "Analysts identify Sensex support and resistance levels"),
        ]
    )

    response = QueryEngine(store).answer("What is support and resistance for Sensex?")

    assert response.grounded is True
    assert response.citations[0].url.endswith("/support")
