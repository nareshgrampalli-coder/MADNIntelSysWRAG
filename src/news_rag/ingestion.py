"""RSS ingestion and domain-specific news fetchers."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import logging
from time import sleep
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from .models import NewsCategory, RawArticle

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str
    category: NewsCategory
    relevance_terms: tuple[str, ...] = ()


class RssSourceAdapter:
    """Fetch RSS XML with bounded retries and parse it into raw articles."""

    def __init__(
        self,
        opener: Callable[..., object] = urlopen,
        retries: int = 2,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._opener = opener
        self._retries = max(0, retries)
        self._timeout_seconds = timeout_seconds

    def fetch(self, source: FeedSource) -> list[RawArticle]:
        payload = self._download(source.url)
        return parse_rss(payload, source)

    def _download(self, url: str) -> bytes:
        request = Request(url, headers={"User-Agent": "news-rag/0.1"})
        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                with self._opener(request, timeout=self._timeout_seconds) as response:
                    return response.read()
            except Exception as error:
                last_error = error
                if attempt == self._retries:
                    break
                sleep(0.2 * (attempt + 1))
        raise RuntimeError(f"Unable to fetch RSS source: {url}") from last_error


def parse_rss(payload: bytes, source: FeedSource) -> list[RawArticle]:
    """Parse RSS 2.0 items, skipping malformed entries."""
    root = ET.fromstring(payload)
    articles: list[RawArticle] = []
    for item in root.findall(".//item"):
        title = _text(item.find("title"))
        url = _text(item.find("link"))
        content = _text(item.find("description"))
        if not title or not url or not content:
            logger.warning("Skipping incomplete RSS item from %s", source.name)
            continue
        published_at = _parse_date(_text(item.find("pubDate")))
        if published_at is None:
            logger.warning("Skipping article with invalid publication date from %s", source.name)
            continue
        articles.append(
            RawArticle(
                title=title,
                url=url,
                source=source.name,
                published_at=published_at,
                content=content,
                category=source.category,
            )
        )
    return articles


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

    def fetch(self) -> list[RawArticle]:
        articles: list[RawArticle] = []
        for source in self.sources:
            try:
                articles.extend(_filter_relevant(self.adapter.fetch(source), source.relevance_terms))
            except Exception:
                logger.exception("Failed to fetch source %s", source.name)
        return deduplicate_articles(articles)


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


def _text(element: ET.Element | None) -> str:
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _normalize(value: str) -> str:
    return " ".join(value.lower().split())


def _filter_relevant(articles: Iterable[RawArticle], relevance_terms: tuple[str, ...]) -> list[RawArticle]:
    if not relevance_terms:
        return list(articles)
    terms = tuple(term.casefold() for term in relevance_terms)
    return [
        article
        for article in articles
        if any(term in f"{article.title} {article.content}".casefold() for term in terms)
    ]
