"""Default and environment-configured RSS sources."""

import os
from urllib.parse import quote_plus

from .ingestion import FeedSource
from .models import NewsCategory


def _google_news_source(category: NewsCategory, query: str) -> FeedSource:
    return FeedSource(
        name=f"Google News - {category.value.title()}",
        url=f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en",
        category=category,
    )


DEFAULT_SOURCES: tuple[FeedSource, ...] = (
    _google_news_source(NewsCategory.TECHNOLOGY, "technology India"),
    _google_news_source(NewsCategory.FINANCE, "finance India markets"),
    _google_news_source(NewsCategory.POLITICS, "politics India"),
)


def _configured_sources(category: NewsCategory) -> tuple[FeedSource, ...]:
    variable = f"NEWS_RAG_{category.value.upper()}_RSS_URLS"
    configured = [url.strip() for url in os.getenv(variable, "").split(",") if url.strip()]
    return tuple(FeedSource(f"Configured {category.value.title()} Feed", url, category) for url in configured)


def sources_for(category: NewsCategory) -> tuple[FeedSource, ...]:
    configured = _configured_sources(category)
    if configured:
        return configured
    return tuple(source for source in DEFAULT_SOURCES if source.category is category)
