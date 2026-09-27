"""RSS source definitions, retrieval, parsing, and article hydration."""

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
import json
import logging
from pathlib import Path
import re
from time import sleep
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from .models import NewsCategory, RawArticle

logger = logging.getLogger(__name__)
MAX_RSS_CANDIDATES_PER_FEED = 15
MAX_ARTICLES_PER_CATEGORY = 3
INDIA_RELEVANCE_TERMS: tuple[str, ...] = (
    "india", "indian", "bharat", "new delhi", "mumbai", "bengaluru", "bangalore",
    "kolkata", "chennai", "hyderabad", "ahmedabad", "pune", "rbi", "sebi", "nse",
    "bse", "sensex", "nifty", "lok sabha", "rajya sabha", "ipl", "bcci",
)
NOISE_PHRASES: tuple[str, ...] = (
    "You are logged in",
    "Loading",
    "LOGOUT",
    "You don't have any Active Subscription",
    "You do not have any Active Subscription",
    "Log in to our website to save your bookmarks",
    "It'll just take a moment",
    "Looks like you have exceeded the limit to bookmark",
    "Remove some to bookmark this image",
)


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
        cache_dir: Path | None = None,
    ) -> None:
        self._opener = opener
        self._retries = max(0, retries)
        self._timeout_seconds = timeout_seconds
        self._cache_dir = cache_dir

    def fetch(self, source: FeedSource) -> list[RawArticle]:
        payload = self._download(source.url)
        candidates = _filter_india_relevant(parse_rss(payload, source))
        relevant_articles: list[RawArticle] = []
        for start in range(0, len(candidates), MAX_ARTICLES_PER_CATEGORY):
            batch = candidates[start : start + MAX_ARTICLES_PER_CATEGORY]
            with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                hydrated = list(executor.map(self._hydrate_article, batch))
            relevant_articles.extend(_filter_relevant(hydrated, source.relevance_terms))
            if len(relevant_articles) >= MAX_ARTICLES_PER_CATEGORY:
                break
        return relevant_articles[:MAX_ARTICLES_PER_CATEGORY]

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
            summary=article.summary,
        )

    def _download(self, url: str) -> bytes:
        cache_body, cache_metadata = self._read_cache(url)
        headers = {"User-Agent": "news-rag/0.1"}
        if cache_metadata.get("etag"):
            headers["If-None-Match"] = cache_metadata["etag"]
        if cache_metadata.get("last_modified"):
            headers["If-Modified-Since"] = cache_metadata["last_modified"]
        request = Request(url, headers=headers)
        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                with self._opener(request, timeout=self._timeout_seconds) as response:
                    payload = response.read()
                    self._write_cache(url, payload, getattr(response, "headers", {}))
                    return payload
            except HTTPError as error:
                if error.code == 304 and cache_body is not None:
                    return cache_body
                last_error = error
                if attempt == self._retries:
                    break
            except Exception as error:
                last_error = error
                if attempt == self._retries:
                    break
                sleep(0.2 * (attempt + 1))
        raise RuntimeError(f"Unable to fetch RSS source: {url}") from last_error

    def _cache_paths(self, url: str) -> tuple[Path, Path] | None:
        if self._cache_dir is None:
            return None
        key = hashlib.sha256(url.encode()).hexdigest()
        return self._cache_dir / f"{key}.body", self._cache_dir / f"{key}.json"

    def _read_cache(self, url: str) -> tuple[bytes | None, dict[str, str]]:
        paths = self._cache_paths(url)
        if paths is None or not paths[0].exists() or not paths[1].exists():
            return None, {}
        try:
            return paths[0].read_bytes(), json.loads(paths[1].read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None, {}

    def _write_cache(self, url: str, payload: bytes, headers: object) -> None:
        paths = self._cache_paths(url)
        if paths is None:
            return
        get_header = getattr(headers, "get", lambda _name: None)
        metadata = {
            key: value
            for key, value in {
                "etag": get_header("ETag"),
                "last_modified": get_header("Last-Modified"),
            }.items()
            if value
        }
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            paths[0].write_bytes(payload)
            paths[1].write_text(json.dumps(metadata), encoding="utf-8")
        except OSError:
            logger.warning("Unable to write HTTP cache for %s", url)


def parse_rss(payload: bytes, source: FeedSource) -> list[RawArticle]:
    """Parse RSS 2.0 items, skipping malformed entries."""
    root = ET.fromstring(payload)
    articles: list[RawArticle] = []
    for item in root.findall(".//item")[:MAX_RSS_CANDIDATES_PER_FEED]:
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
                summary=content,
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
        self._ignored_tags: list[str] = []
        self._content_depth = 0
        self._has_content_container = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.casefold(): (value or "").casefold() for name, value in attrs}
        marker = f"{attributes.get('id', '')} {attributes.get('class', '')}"
        is_noise = bool(re.search(
            r"\b(?:ad|ads|advert|advertisement|banner|promo|promotion|recommended|related|social|subscribe|subscription|newsletter|outbrain|taboola)\b",
            marker,
        ))
        if tag in {"script", "style", "nav", "footer", "header", "aside", "form"} or is_noise:
            self._ignored_depth += 1
            self._ignored_tags.append(tag)
        if tag in {"article", "main"}:
            self._content_depth += 1
            self._has_content_container = True

    def handle_endtag(self, tag: str) -> None:
        if tag in self._ignored_tags:
            self._ignored_depth -= 1
            self._ignored_tags.remove(tag)
        if tag in {"article", "main"} and self._content_depth:
            self._content_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth and (not self._has_content_container or self._content_depth):
            self.parts.append(data)


def _extract_article_text(payload: bytes) -> str:
    parser = _ArticleTextExtractor()
    parser.feed(payload.decode("utf-8", errors="replace"))
    text = " ".join(" ".join(parser.parts).split())
    for phrase in NOISE_PHRASES:
        text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)
    text = re.sub(
        r"(?:Advertisement|Sponsored|Subscribe to our newsletter|Follow us on social media):?[^.]*\.?",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    return " ".join(text.split())


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


def _filter_relevant(articles: Iterable[RawArticle], relevance_terms: tuple[str, ...]) -> list[RawArticle]:
    if not relevance_terms:
        return list(articles)
    terms = tuple(term.casefold() for term in relevance_terms)
    return [
        article
        for article in articles
        if any(term in f"{article.title} {article.content}".casefold() for term in terms)
    ]


def _filter_india_relevant(articles: Iterable[RawArticle]) -> list[RawArticle]:
    terms = tuple(term.casefold() for term in INDIA_RELEVANCE_TERMS)
    return [
        article
        for article in articles
        if any(term in f"{article.title} {article.summary}".casefold() for term in terms)
    ]