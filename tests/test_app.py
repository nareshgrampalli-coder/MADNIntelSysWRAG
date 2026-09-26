from datetime import date, datetime, timezone

from app import apply_filters, build_todays_briefing, citation_lines
from news_rag.models import ArticleChunk, NewsCategory, QueryResponse, SourceCitation
from news_rag.vector_store import JsonVectorStore


def test_apply_filters_adds_category_and_date_constraints() -> None:
    result = apply_filters("What happened?", NewsCategory.FINANCE, date(2026, 9, 20))

    assert result == "What happened? (finance, since 2026-09-20)"


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
        "[Policy update](https://example.com/story) - Example News, 2026-09-26"
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
            )
        ]
    )

    briefing = build_todays_briefing(store, datetime(2026, 9, 26, 12, tzinfo=timezone.utc))

    assert [category for category, _ in briefing] == [NewsCategory.FINANCE]
