"""Default and environment-configured RSS sources."""

import os

from .ingestion import FeedSource
from .models import NewsCategory


RELEVANCE_TERMS: dict[NewsCategory, tuple[str, ...]] = {
    NewsCategory.TECHNOLOGY: ("technology", "software", "ai", "cybersecurity", "startup", "digital"),
    NewsCategory.FINANCE: ("market", "rbi", "bank", "finance", "earnings", "stocks", "economy"),
    NewsCategory.POLITICS: ("government", "minister", "election", "policy", "parliament", "politics"),
    NewsCategory.STOCKS: ("india", "nse", "bse", "sensex", "nifty", "stocks", "shares"),
}


PUBLISHER_FEEDS: tuple[tuple[str, str], ...] = (
    ("Indian Express", "https://indianexpress.com/feed/"),
    ("NDTV", "https://feeds.feedburner.com/ndtvnews-top-stories"),
    ("The Hindu", "https://www.thehindu.com/feeder/default.rss"),
    ("LiveMint", "https://www.livemint.com/rss/markets"),
)
YAHOO_FINANCE_FEED = ("Yahoo Finance", "https://finance.yahoo.com/rss/")


def _publisher_source(category: NewsCategory, publisher: str, url: str) -> FeedSource:
    return FeedSource(
        name=f"{publisher} - {category.value.title()}",
        url=url,
        category=category,
        relevance_terms=RELEVANCE_TERMS[category],
    )


DEFAULT_SOURCES: tuple[FeedSource, ...] = tuple(
    _publisher_source(category, publisher, url)
    for category in NewsCategory
    for publisher, url in (
        (YAHOO_FINANCE_FEED,) + PUBLISHER_FEEDS[:3]
        + PUBLISHER_FEEDS[3:]
        if category is NewsCategory.FINANCE
        else PUBLISHER_FEEDS
    )
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
