"""RSS ingestion and domain-specific news fetchers."""

from collections.abc import Iterable
import hashlib
import logging
import re

from .models import NewsCategory, RawArticle
from .rss import (
    INDIA_RELEVANCE_TERMS,
    MAX_ARTICLES_PER_CATEGORY,
    MAX_RSS_CANDIDATES_PER_FEED,
    NOISE_PHRASES,
    FeedSource,
    RssSourceAdapter,
    _filter_india_relevant,
    _filter_relevant,
    parse_rss,
)

logger = logging.getLogger(__name__)
from .rss import (
    FeedSource,
    RssSourceAdapter,
    _filter_india_relevant,
    _filter_relevant,
    parse_rss,
)


def deduplicate_articles(articles: Iterable[RawArticle]) -> list[RawArticle]:
    """Keep the first article for each URL and normalized content hash."""
    seen_urls: set[str] = set()
    seen_content: set[str] = set()
    unique: list[RawArticle] = []
    for article in articles:
        content_hash = hashlib.sha256(_normalize(article.content).encode()).hexdigest()
        if article.url in seen_urls or content_hash in seen_content:
            continue
        seen_urls.add(article.url)
        seen_content.add(content_hash)
        unique.append(article)
    return unique


class DomainFetcher:
    def __init__(self, sources: Iterable[FeedSource], adapter: RssSourceAdapter | None = None) -> None:
        self.sources = tuple(sources)
        self.adapter = adapter or RssSourceAdapter()
        self.errors: list[str] = []

    def fetch(self) -> list[RawArticle]:
        self.errors.clear()
        articles: list[RawArticle] = []
        for source in self.sources:
            try:
                fetched = self.adapter.fetch(source)
                relevant = _filter_relevant(fetched, source.relevance_terms)
                articles.extend(_filter_india_relevant(relevant))
            except Exception:
                logger.exception("Failed to fetch source %s", source.name)
                self.errors.append(f"{source.name}: failed to fetch {source.url}")
        unique_articles = deduplicate_articles(articles)
        unique_articles.sort(key=lambda article: article.published_at, reverse=True)
        return unique_articles[:MAX_ARTICLES_PER_CATEGORY]


class TechnologyFetcher(DomainFetcher):
    def __init__(self, sources: Iterable[FeedSource] = (), adapter: RssSourceAdapter | None = None) -> None:
        super().__init__(sources, adapter)


class FinanceFetcher(DomainFetcher):
    def __init__(self, sources: Iterable[FeedSource] = (), adapter: RssSourceAdapter | None = None) -> None:
        super().__init__(sources, adapter)


class PoliticsFetcher(DomainFetcher):
    def __init__(self, sources: Iterable[FeedSource] = (), adapter: RssSourceAdapter | None = None) -> None:
        super().__init__(sources, adapter)


class StocksFetcher(DomainFetcher):
    def __init__(self, sources: Iterable[FeedSource] = (), adapter: RssSourceAdapter | None = None) -> None:
        super().__init__(sources, adapter)


class SportsFetcher(DomainFetcher):
    def __init__(self, sources: Iterable[FeedSource] = (), adapter: RssSourceAdapter | None = None) -> None:
        super().__init__(sources, adapter)


def _normalize(value: str) -> str:
    return " ".join(value.lower().split())
