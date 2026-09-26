"""Default and environment-configured RSS sources."""

import os

from .ingestion import FeedSource
from .models import NewsCategory


RELEVANCE_TERMS: dict[NewsCategory, tuple[str, ...]] = {
    NewsCategory.TECHNOLOGY: ("technology", "software", "ai", "cybersecurity", "startup", "digital"),
    NewsCategory.FINANCE: ("market", "rbi", "bank", "finance", "earnings", "stocks", "economy"),
    NewsCategory.POLITICS: ("government", "minister", "election", "policy", "parliament", "politics"),
    NewsCategory.STOCKS: ("nse", "bse", "sensex", "nifty", "stocks", "shares"),
    NewsCategory.SPORTS: ("sport", "cricket", "football", "tennis", "match", "league", "player"),
}


LIVEMINT_FEEDS: dict[NewsCategory, tuple[str, str]] = {
    NewsCategory.TECHNOLOGY: ("LiveMint", "https://www.livemint.com/rss/news"),
    NewsCategory.FINANCE: ("LiveMint", "https://www.livemint.com/rss/money"),
    NewsCategory.POLITICS: ("LiveMint", "https://www.livemint.com/rss/politics"),
    NewsCategory.STOCKS: ("LiveMint", "https://www.livemint.com/rss/markets"),
    NewsCategory.SPORTS: ("LiveMint", "https://www.livemint.com/rss/sports"),
}
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
        (YAHOO_FINANCE_FEED, LIVEMINT_FEEDS[category])
        if category is NewsCategory.FINANCE
        else (LIVEMINT_FEEDS[category],)
    )
)


def _configured_sources(category: NewsCategory) -> tuple[FeedSource, ...]:
    prefix = f"NEWS_RAG_{category.value.upper()}"
    configured = [url.strip() for url in os.getenv(f"{prefix}_RSS_URLS", "").split(",") if url.strip()]
    approved = [url.strip() for url in os.getenv(f"{prefix}_APPROVED_RSS_URLS", "").split(",") if url.strip()]
    urls = [url for url in (approved or configured) if "news.google.com" not in url.casefold()]
    return tuple(
        FeedSource(f"Configured {category.value.title()} Feed", url, category, RELEVANCE_TERMS[category])
        for url in urls
    )


def sources_for(category: NewsCategory) -> tuple[FeedSource, ...]:
    configured = _configured_sources(category)
    if configured:
        return configured
    return tuple(source for source in DEFAULT_SOURCES if source.category is category)
