"""Date-aware, citation-preserving RAG query orchestration."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

from .models import ArticleChunk, NewsCategory, QueryResponse, SourceCitation
from .vector_store import JsonVectorStore


@dataclass(frozen=True)
class QueryFilters:
    category: NewsCategory | None = None
    published_after: datetime | None = None


class QueryInterpreter:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def interpret(self, question: str) -> QueryFilters:
        normalized = question.casefold()
        category = next(
            (candidate for candidate in NewsCategory if candidate.value in normalized),
            None,
        )
        now = self.clock()
        if "today" in normalized:
            published_after = now - timedelta(days=1)
        elif "this week" in normalized or "last 7 days" in normalized:
            published_after = now - timedelta(days=7)
        elif "this month" in normalized:
            published_after = now - timedelta(days=30)
        else:
            published_after = _explicit_date(normalized)
        return QueryFilters(category=category, published_after=published_after)


class ExtractiveAnswerGenerator:
    """Provider-neutral fallback that answers strictly from retrieved chunks."""

    def generate(self, question: str, chunks: list[ArticleChunk]) -> str:
        if not chunks:
            return "I don't have news on that."
        excerpts = [chunk.text.rstrip(". ") + "." for chunk in chunks[:3]]
        return " ".join(excerpts)


class QueryEngine:
    def __init__(
        self,
        store: JsonVectorStore,
        interpreter: QueryInterpreter | None = None,
        generator: ExtractiveAnswerGenerator | None = None,
        retrieval_limit: int = 8,
    ) -> None:
        self.store = store
        self.interpreter = interpreter or QueryInterpreter()
        self.generator = generator or ExtractiveAnswerGenerator()
        self.retrieval_limit = retrieval_limit

    def answer(self, question: str) -> QueryResponse:
        filters = self.interpreter.interpret(question)
        chunks = self.store.query(
            question,
            category=filters.category,
            published_after=filters.published_after,
            limit=self.retrieval_limit,
        )
        chunks.sort(key=lambda chunk: chunk.published_at, reverse=True)
        if not chunks:
            return QueryResponse(answer="I don't have news on that.")
        citations = _citations(chunks)
        return QueryResponse(
            answer=self.generator.generate(question, chunks),
            citations=tuple(citations),
            grounded=True,
        )


def _explicit_date(question: str) -> datetime | None:
    match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", question)
    if not match:
        return None
    year, month, day = (int(value) for value in match.groups())
    return datetime(year, month, day, tzinfo=timezone.utc)


def _citations(chunks: list[ArticleChunk]) -> list[SourceCitation]:
    citations: list[SourceCitation] = []
    seen_urls: set[str] = set()
    for chunk in chunks:
        if chunk.article_url in seen_urls:
            continue
        seen_urls.add(chunk.article_url)
        citations.append(
            SourceCitation(
                title=chunk.metadata.get("title", "Untitled article"),
                source=chunk.source,
                url=chunk.article_url,
                published_at=chunk.published_at,
            )
        )
    return citations
