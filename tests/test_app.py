from datetime import date, datetime, timezone

from app import apply_filters, build_sample_questions, build_todays_briefing, citation_lines
from news_rag.models import ArticleChunk, NewsCategory, QueryResponse, SourceCitation
from news_rag.app_support import verify_retrieval_quality
from news_rag.query_engine import QueryEngine
from news_rag.ui_helpers import trim_sentence
from news_rag.vector_store import JsonVectorStore


def test_apply_filters_adds_category_and_date_constraints() -> None:
    result = apply_filters("What happened?", NewsCategory.FINANCE, date(2026, 9, 20))

    assert result == "What happened? (finance, since 2026-09-20)"


def test_trim_sentence_keeps_short_lines_and_cuts_at_sentence_boundary() -> None:
    short = "Nifty gained today"
    long_line = "First complete sentence here. " + "Second sentence. " * 40

    assert trim_sentence(short) == short
    trimmed = trim_sentence(long_line, limit=80)
    assert len(trimmed) <= 80
    assert "..." not in trimmed
    assert trimmed.endswith("sentence")
    assert trimmed.startswith("First complete sentence here")


def test_trim_sentence_truncates_single_long_sentence_at_word_boundary() -> None:
    line = "word " * 100

    trimmed = trim_sentence(line, limit=80)

    assert len(trimmed) <= 84
    assert trimmed.endswith("...")


def test_citation_lines_include_source_links_and_dates() -> None:
    response = QueryResponse(
        answer="Answer",
        grounded=True,
        citations=(
            SourceCitation(
                title="Policy update",
                source="Example News",
                url="https://example.com/story",
                published_at=__import__("datetime").datetime(2026, 9, 26),
            ),
        ),
    )

    assert citation_lines(response) == [
        "[Policy update](https://example.com/story) - Example News, 26-Sep-2026"
    ]


def test_citations_keep_article_specific_summaries(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert(
        [
            ArticleChunk(
                chunk_id="one",
                article_url="https://example.com/one",
                text="First article details",
                chunk_index=0,
                category=NewsCategory.FINANCE,
                source="Example News",
                published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
                metadata={"title": "First", "summary": "First article summary"},
            ),
            ArticleChunk(
                chunk_id="two",
                article_url="https://example.com/two",
                text="Second article details",
                chunk_index=0,
                category=NewsCategory.FINANCE,
                source="Example News",
                published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
                metadata={"title": "Second", "summary": "Second article summary"},
            ),
        ]
    )

    response = QueryEngine(store).answer("finance", relevance_threshold=0.0)

    assert [citation.summary for citation in response.citations] == [
        "First article summary",
        "Second article summary",
    ]


def test_build_todays_briefing_returns_grounded_domains(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert(
        [
            ArticleChunk(
                chunk_id="finance",
                article_url="https://example.com/finance",
                text="RBI announced a finance policy update today",
                chunk_index=0,
                category=NewsCategory.FINANCE,
                source="Example News",
                published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
                metadata={"title": "Finance update"},
            ),
            ArticleChunk(
                chunk_id="stocks",
                article_url="https://example.com/stocks",
                text="Indian stocks gained today",
                chunk_index=0,
                category=NewsCategory.STOCKS,
                source="Example News",
                published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
                metadata={"title": "Stocks update"},
            ),
        ]
    )

    briefing = build_todays_briefing(store, datetime(2026, 9, 26, 12, tzinfo=timezone.utc))

    assert [category for category, _ in briefing] == [NewsCategory.FINANCE, NewsCategory.STOCKS]


def test_verify_retrieval_quality_reports_category_coverage(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert(
        [
            ArticleChunk(
                chunk_id="finance",
                article_url="https://example.com/finance",
                text="India finance markets and RBI policy update",
                chunk_index=0,
                category=NewsCategory.FINANCE,
                source="Example News",
                published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
                metadata={"title": "India finance update"},
            )
        ]
    )

    coverage = verify_retrieval_quality(store)

    assert coverage[NewsCategory.FINANCE] > 0
    assert coverage[NewsCategory.SPORTS] == 0


def test_build_todays_briefing_excludes_stale_articles(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert(
        [
            ArticleChunk(
                chunk_id="stale-stocks",
                article_url="https://example.com/stale-stocks",
                text="Sensex and Nifty closed higher",
                chunk_index=0,
                category=NewsCategory.STOCKS,
                source="Example News",
                published_at=datetime(2026, 7, 30, tzinfo=timezone.utc),
                metadata={"title": "Stock Market Today July 30"},
            )
        ]
    )

    briefing = build_todays_briefing(store, datetime(2026, 9, 6, 12, tzinfo=timezone.utc))

    assert briefing == []


def test_build_todays_briefing_does_not_use_previous_day_when_today_is_empty(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert(
        [
            ArticleChunk(
                chunk_id="previous-day-stocks",
                article_url="https://example.com/previous-day-stocks",
                text="Sensex and Nifty closed higher",
                chunk_index=0,
                category=NewsCategory.STOCKS,
                source="Example News",
                published_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
                metadata={"title": "Stock Market Update September 5"},
            )
        ]
    )

    briefing = build_todays_briefing(store, datetime(2026, 9, 6, 12, tzinfo=timezone.utc))

    assert briefing == []


def test_sample_questions_use_indexed_article_titles(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert(
        [
            ArticleChunk(
                chunk_id="stocks",
                article_url="https://example.com/stocks",
                text="Nifty gained after strong market activity",
                chunk_index=0,
                category=NewsCategory.STOCKS,
                source="Example News",
                published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
                metadata={"title": "Nifty gains after market rally"},
            )
        ]
    )

    questions = build_sample_questions(store)

    assert questions[NewsCategory.STOCKS] == (
        "What happened in Nifty gains after market rally?",
    )
