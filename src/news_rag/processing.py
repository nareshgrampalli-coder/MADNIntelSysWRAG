"""Deterministic article cleaning, enrichment, and chunking."""

from collections.abc import Iterable
from html.parser import HTMLParser
import hashlib
import re

from .models import ArticleChunk, NewsCategory, ProcessedArticle, RawArticle

_WORD_RE = re.compile(r"\b[\w'-]+\b")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_TAG_RULES: dict[str, tuple[str, ...]] = {
    "markets": ("market", "stock", "share", "equity", "index"),
    "policy": ("policy", "regulation", "rate", "government", "bill"),
    "technology": ("technology", "software", "chip", "artificial intelligence", "cyber"),
    "business": ("company", "business", "revenue", "earnings", "startup"),
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "nav", "footer", "header", "aside"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav", "footer", "header", "aside"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def clean_text(content: str) -> str:
    """Remove HTML and common whitespace noise from article content."""
    parser = _TextExtractor()
    parser.feed(content)
    text = " ".join(parser.parts) if parser.parts else content
    return " ".join(text.split()).strip()


def summarize(text: str, sentence_limit: int = 2) -> str:
    sentences = [sentence.strip() for sentence in _SENTENCE_RE.split(text) if sentence.strip()]
    return " ".join(sentences[:sentence_limit]) or text[:280].strip()


def derive_tags(text: str, category: NewsCategory) -> tuple[str, ...]:
    normalized = text.casefold()
    tags = [category.value]
    tags.extend(name for name, keywords in _TAG_RULES.items() if any(keyword in normalized for keyword in keywords))
    return tuple(dict.fromkeys(tags))


def extract_entities(text: str) -> tuple[str, ...]:
    candidates = re.findall(r"\b[A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*)*", text)
    ignored = {"The", "A", "An", "This", "That", "According"}
    return tuple(dict.fromkeys(candidate.strip() for candidate in candidates if candidate not in ignored))


def process_article(article: RawArticle) -> ProcessedArticle:
    cleaned = clean_text(article.content)
    source_summary = clean_text(article.summary)
    summary = summarize(source_summary) if source_summary else summarize(cleaned)
    return ProcessedArticle(
        article=RawArticle(
            title=article.title,
            url=article.url,
            source=article.source,
            published_at=article.published_at,
            content=cleaned,
            category=article.category,
            summary=source_summary or summary,
        ),
        summary=summary,
        tags=derive_tags(cleaned, article.category),
        entities=extract_entities(cleaned),
    )


def chunk_article(article: ProcessedArticle, max_words: int = 400) -> list[ArticleChunk]:
    """Split processed content into word-bounded chunks with provenance."""
    if max_words < 1:
        raise ValueError("max_words must be positive")
    words = _WORD_RE.findall(article.article.content)
    chunks: list[ArticleChunk] = []
    for index in range(0, len(words), max_words):
        text = " ".join(words[index : index + max_words])
        chunk_index = index // max_words
        digest = hashlib.sha256(f"{article.article.url}:{chunk_index}".encode()).hexdigest()[:16]
        chunks.append(
            ArticleChunk(
                chunk_id=digest,
                article_url=article.article.url,
                text=text,
                chunk_index=chunk_index,
                category=article.article.category,
                source=article.article.source,
                published_at=article.article.published_at,
                metadata={
                    "title": article.article.title,
                    "summary": article.summary,
                    "tags": ",".join(article.tags),
                    "entities": ",".join(article.entities),
                },
            )
        )
    return chunks


def process_and_chunk(articles: Iterable[RawArticle], max_words: int = 400) -> list[ArticleChunk]:
    chunks: list[ArticleChunk] = []
    for article in articles:
        chunks.extend(chunk_article(process_article(article), max_words=max_words))
    return chunks
