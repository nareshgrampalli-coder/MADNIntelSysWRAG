"""RSS ingestion and domain-specific news fetchers."""

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
import logging
from time import sleep
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from .models import NewsCategory, RawArticle

logger = logging.getLogger(__name__)
MAX_ARTICLES_PER_FEED = 3
MAX_ARTICLES_PER_CATEGORY = 3


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
        articles = parse_rss(payload, source)
        with ThreadPoolExecutor(max_workers=min(8, max(1, len(articles)))) as executor:
            return list(executor.map(self._hydrate_article, articles))

    def _hydrate_article(self, article: RawArticle) -> RawArticle:
        try:
            page = self._download(article.url)
            content = _extract_article_text(page)
        except Exception:
            return article
        if not content:
            return article
        return RawArticle(
            title=article.title,
            url=article.url,
            source=article.source,
            published_at=article.published_at,
            content=content,
            category=article.category,
        )

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
    for item in root.findall(".//item")[:MAX_ARTICLES_PER_FEED]:
        title = _text(item.find("title"))
        url = _text(item.find("link"))
        content = _rss_content(item) or title
        if not title or not url:
            logger.warning("Skipping incomplete RSS item from %s", source.name)
            continue
        published_at = _parse_date(_text(item.find("pubDate")))
        if published_at is None:
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


def _rss_content(item: ET.Element) -> str:
    """Return the first usable summary/body field from an RSS item."""
    content = _text(item.find("description"))
    if content:
        return content
    for child in item:
        if child.tag.rsplit("}", 1)[-1] == "encoded":
            return _text(child)
    return ""


class _ArticleTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "nav", "footer", "header", "aside", "form"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav", "footer", "header", "aside", "form"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def _extract_article_text(payload: bytes) -> str:
    parser = _ArticleTextExtractor()
    parser.feed(payload.decode("utf-8", errors="replace"))
    return " ".join(" ".join(parser.parts).split())


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


def _text(element: ET.Element | None) -> str:
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
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
