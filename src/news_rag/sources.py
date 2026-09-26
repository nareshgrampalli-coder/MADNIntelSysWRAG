"""Default and environment-configured RSS sources."""

import os
from urllib.parse import quote_plus

from .ingestion import FeedSource
from .models import NewsCategory


RELEVANCE_TERMS: dict[NewsCategory, tuple[str, ...]] = {
    NewsCategory.TECHNOLOGY: ("technology", "software", "ai", "cybersecurity", "startup", "digital"),
    NewsCategory.FINANCE: ("market", "rbi", "bank", "finance", "earnings", "stocks", "economy"),
    NewsCategory.POLITICS: ("government", "minister", "election", "policy", "parliament", "politics"),
    NewsCategory.STOCKS: ("india", "nse", "bse", "sensex", "nifty", "stocks", "shares"),
}


def _google_news_source(category: NewsCategory, query: str) -> FeedSource:
    return FeedSource(
        name=f"Google News - {category.value.title()}",
        url=f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en",
        category=category,
        relevance_terms=RELEVANCE_TERMS[category],
    )


DEFAULT_SOURCES: tuple[FeedSource, ...] = (
    _google_news_source(NewsCategory.TECHNOLOGY, "technology India"),
    _google_news_source(NewsCategory.TECHNOLOGY, "AI cybersecurity startups India"),
    _google_news_source(NewsCategory.TECHNOLOGY, "software digital innovation India"),
    _google_news_source(NewsCategory.TECHNOLOGY, "technology companies India funding"),
    _google_news_source(NewsCategory.FINANCE, "finance India markets"),
    _google_news_source(NewsCategory.FINANCE, "RBI economy earnings India"),
    _google_news_source(NewsCategory.FINANCE, "Indian banking financial policy"),
    _google_news_source(NewsCategory.FINANCE, "India business corporate finance"),
    _google_news_source(NewsCategory.POLITICS, "politics India"),
    _google_news_source(NewsCategory.POLITICS, "India government parliament policy"),
    _google_news_source(NewsCategory.POLITICS, "India minister political decision"),
    _google_news_source(NewsCategory.POLITICS, "India law election public policy"),
    _google_news_source(NewsCategory.STOCKS, "India stock market NSE BSE Nifty Sensex"),
    _google_news_source(NewsCategory.STOCKS, "Indian shares market closing today"),
    _google_news_source(NewsCategory.STOCKS, "Nifty Sensex stock market analysis India"),
    _google_news_source(NewsCategory.STOCKS, "BSE NSE Indian stocks business news"),
)


def _configured_sources(category: NewsCategory) -> tuple[FeedSource, ...]:
    prefix = f"NEWS_RAG_{category.value.upper()}"
    configured = [url.strip() for url in os.getenv(f"{prefix}_RSS_URLS", "").split(",") if url.strip()]
    approved = [url.strip() for url in os.getenv(f"{prefix}_APPROVED_RSS_URLS", "").split(",") if url.strip()]
    urls = approved or configured
    return tuple(
        FeedSource(f"Configured {category.value.title()} Feed", url, category, RELEVANCE_TERMS[category])
        for url in urls
    )


def sources_for(category: NewsCategory) -> tuple[FeedSource, ...]:
    configured = _configured_sources(category)
    if configured:
        return configured
    return tuple(source for source in DEFAULT_SOURCES if source.category is category)
