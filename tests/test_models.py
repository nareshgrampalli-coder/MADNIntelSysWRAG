from datetime import datetime, timezone

from news_rag.models import NewsCategory, QueryResponse, RawArticle


def test_raw_article_preserves_category_and_provenance() -> None:
    published_at = datetime(2026, 9, 26, tzinfo=timezone.utc)
    article = RawArticle(
        title="Example headline",
        url="https://example.com/article",
        source="Example News",
        published_at=published_at,
        content="Article content",
        category=NewsCategory.TECHNOLOGY,
    )

    assert article.category is NewsCategory.TECHNOLOGY
    assert article.published_at == published_at
    assert article.url.startswith("https://")


def test_query_response_defaults_to_ungrounded_without_citations() -> None:
    response = QueryResponse(answer="I don't have news on that")

    assert response.grounded is False
    assert response.citations == ()
