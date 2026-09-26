"""Core typed contracts shared by the news pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class NewsCategory(StrEnum):
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    POLITICS = "politics"
    STOCKS = "stocks"


@dataclass(frozen=True)
class RawArticle:
    title: str
    url: str
    source: str
    published_at: datetime
    content: str
    category: NewsCategory


@dataclass(frozen=True)
class ProcessedArticle:
    article: RawArticle
    summary: str
    tags: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArticleChunk:
    chunk_id: str
    article_url: str
    text: str
    chunk_index: int
    category: NewsCategory
    source: str
    published_at: datetime
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceCitation:
    title: str
    source: str
    url: str
    published_at: datetime
    summary: str = ""


@dataclass(frozen=True)
class QueryResponse:
    answer: str
    citations: tuple[SourceCitation, ...] = ()
    grounded: bool = False
