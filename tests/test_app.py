from contextlib import nullcontext
from datetime import date, datetime, timezone

from app import apply_filters, build_sample_questions, build_todays_briefing, citation_lines, scheduled_ingestion_interval
from news_rag.models import ArticleChunk, NewsCategory, QueryResponse, SourceCitation
from news_rag.app_support import (
    build_contextual_question,
    initialize_ingestion_status,
    retrieval_metrics,
    verify_grounding_quality,
    verify_query_interpretation,
    verify_retrieval_quality,
)
from news_rag.query_engine import QueryEngine
from news_rag.ui_helpers import format_chat_answer, trim_sentence
from news_rag.vector_store import EmbeddingProviderMismatch, HashEmbeddingProvider, JsonVectorStore


def test_apply_filters_adds_category_and_date_constraints() -> None:
    result = apply_filters("What happened?", NewsCategory.FINANCE, date(2026, 9, 20))

    assert result == "What happened? (finance, since 2026-09-20)"


def test_scheduled_ingestion_interval_is_optional_and_validated(monkeypatch) -> None:
    monkeypatch.delenv("NEWS_RAG_AUTO_INGEST_SECONDS", raising=False)
    assert scheduled_ingestion_interval() is None

    monkeypatch.setenv("NEWS_RAG_AUTO_INGEST_SECONDS", "3600")
    assert scheduled_ingestion_interval() == 3600.0


def test_new_page_session_requires_ingestion_even_when_index_already_exists() -> None:
    session_state = {}

    initialize_ingestion_status(session_state)

    assert session_state["ingestion_completed"] is False

    session_state["ingestion_completed"] = True
    initialize_ingestion_status(session_state)

    assert session_state["ingestion_completed"] is True


def test_trim_sentence_keeps_short_lines_and_cuts_at_sentence_boundary() -> None:
    short = "Nifty gained today"
    long_line = "First complete sentence here. " + "Second sentence. " * 40

    assert trim_sentence(short) == short
    trimmed = trim_sentence(long_line, limit=80)
    assert len(trimmed) <= 80
    assert "..." not in trimmed
    assert trimmed.endswith("sentence.")
    assert trimmed.startswith("First complete sentence here")


def test_trim_sentence_truncates_single_long_sentence_at_word_boundary() -> None:
    line = "word " * 100

    trimmed = trim_sentence(line, limit=80)

    assert len(trimmed) <= 84
    assert trimmed.endswith("...")


def test_trim_sentence_preserves_a_complete_sentence_longer_than_limit() -> None:
    line = "A complete sentence that is longer than the configured display limit " * 4 + "."

    assert trim_sentence(line, limit=80) == line


def test_trim_sentence_preserves_terminal_punctuation_on_short_lines() -> None:
    assert trim_sentence("RBI cut the repo rate by 25 basis points.") == (
        "RBI cut the repo rate by 25 basis points."
    )
    assert trim_sentence("Markets closed higher today!") == "Markets closed higher today!"


def test_format_chat_answer_keeps_bullets_for_single_topic_answers() -> None:
    answer = "- RBI held the policy rate steady.\n- Markets reacted positively."

    assert format_chat_answer(answer) == answer


def test_format_chat_answer_preserves_category_headers_and_bullets() -> None:
    answer = (
        "**Finance**\n- RBI held the policy rate steady.\n\n"
        "**Technology**\n- New chips announced today."
    )

    formatted = format_chat_answer(answer)

    assert "**Finance**" in formatted
    assert "**Technology**" in formatted
    assert "- RBI held the policy rate steady." in formatted
    assert "- New chips announced today." in formatted


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


def test_build_todays_briefing_limits_distinct_articles_not_chunks(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    chunks = [
        ArticleChunk(
            chunk_id=f"long-story-{index}",
            article_url="https://example.com/long-story",
            text="India cricket sports update with match details.",
            chunk_index=index,
            category=NewsCategory.SPORTS,
            source="Example News",
            published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
            metadata={"title": "Latest sports news from India"},
        )
        for index in range(8)
    ]
    chunks.extend(
        ArticleChunk(
            chunk_id=f"story-{index}",
            article_url=f"https://example.com/story-{index}",
            text="India cricket sports update with match details.",
            chunk_index=0,
            category=NewsCategory.SPORTS,
            source="Example News",
            published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
            metadata={"title": f"Latest sports news {index} from India"},
        )
        for index in range(2)
    )
    store.upsert(chunks)

    briefing = build_todays_briefing(store, datetime(2026, 9, 26, 12, tzinfo=timezone.utc))

    sports_response = next(response for category, response in briefing if category is NewsCategory.SPORTS)
    assert len(sports_response.citations) == 3
    assert len({citation.url for citation in sports_response.citations}) == 3


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


def test_retrieval_metrics_summarize_source_and_category_coverage() -> None:
    metrics = retrieval_metrics(
        {
            NewsCategory.FINANCE: 2,
            NewsCategory.STOCKS: 1,
            NewsCategory.SPORTS: 0,
        }
    )

    assert metrics == {
        "total_sources": 3,
        "covered_categories": 2,
        "category_count": 3,
        "coverage_percent": 66.7,
    }


def test_verify_query_interpretation_covers_categories_dates_and_context() -> None:
    checks = verify_query_interpretation()

    assert len(checks) == len(NewsCategory) + 3
    assert all(checks.values())


def test_build_contextual_question_handles_followups_and_repeats() -> None:
    messages = [{"role": "user", "content": "What is the Nifty 50 target?"}]

    assert build_contextual_question(messages, "What are the risks?") == (
        "What is the Nifty 50 target? What are the risks?"
    )
    assert build_contextual_question(messages, "What is the Nifty 50 target?") == messages[0]["content"]


def test_build_contextual_question_does_not_merge_unrelated_questions() -> None:
    messages = [{"role": "user", "content": "What is news with Virat Kohli?"}]

    assert build_contextual_question(messages, "When is SAIL giving dividend?") == (
        "When is SAIL giving dividend?"
    )


def test_verify_grounding_quality_checks_citations_and_refusal(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert(
        [
            ArticleChunk(
                chunk_id="grounded",
                article_url="https://example.com/grounded",
                text="India markets opened higher today",
                chunk_index=0,
                category=NewsCategory.FINANCE,
                source="Example News",
                published_at=datetime(2026, 9, 27, tzinfo=timezone.utc),
                metadata={"title": "India markets update"},
            )
        ]
    )

    checks = verify_grounding_quality(store)

    assert checks == {"supported:cited": True, "unsupported:refused": True}


def test_briefing_shows_reindex_instructions_for_embedding_mismatch() -> None:
    from news_rag.briefing_view import render_todays_briefing

    class FakeStreamlit:
        warnings: list[str] = []

        def subheader(self, text: str) -> None:
            pass

        def warning(self, text: str) -> None:
            self.warnings.append(text)

        def spinner(self, text: str):
            return nullcontext()

    class MismatchedStore:
        def query(self, *args, **kwargs):
            raise EmbeddingProviderMismatch("Stored vectors use a different embedding provider.")

        def count(self):
            return 1

    st = FakeStreamlit()

    render_todays_briefing(st, MismatchedStore(), lambda *args: None)

    assert "Reset Indexed chunks data" in st.warnings[0]
    assert "Run ingestion" in st.warnings[0]


def test_verify_grounding_quality_refuses_unrelated_article_with_common_word_overlap(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    store.upsert(
        [
            ArticleChunk(
                chunk_id="asian-games",
                article_url="https://example.com/asian-games",
                text="This event coverage describes the Asian Games competition.",
                chunk_index=0,
                category=NewsCategory.SPORTS,
                source="Example News",
                published_at=datetime(2026, 9, 27, tzinfo=timezone.utc),
                metadata={"title": "Asian Games event coverage"},
            )
        ]
    )

    checks = verify_grounding_quality(store)

    assert checks["unsupported:refused"] is True


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
