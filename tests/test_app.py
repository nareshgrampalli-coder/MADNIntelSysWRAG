from datetime import date

from app import apply_filters, citation_lines
from news_rag.models import QueryResponse, SourceCitation
from news_rag.models import NewsCategory


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
