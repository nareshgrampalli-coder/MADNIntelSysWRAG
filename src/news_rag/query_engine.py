"""Date-aware, citation-preserving RAG query orchestration."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

from .models import ArticleChunk, NewsCategory, QueryResponse, SourceCitation
from .vector_store import VectorStore


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
        if category is None and re.search(r"\bstock(?:s)?\b", normalized):
            category = NewsCategory.STOCKS
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
        if "summar" in question.casefold() or "bullet" in question.casefold():
            return "\n".join(f"- {excerpt}" for excerpt in excerpts)
        return " ".join(excerpts)


class QueryEngine:
    def __init__(
        self,
        store: VectorStore,
        interpreter: QueryInterpreter | None = None,
        generator: ExtractiveAnswerGenerator | None = None,
        retrieval_limit: int = 12,
    ) -> None:
        self.store = store
        self.interpreter = interpreter or QueryInterpreter()
        self.generator = generator or ExtractiveAnswerGenerator()
        self.retrieval_limit = retrieval_limit

    def answer(self, question: str, relevance_threshold: float = 0.5) -> QueryResponse:
        filters = self.interpreter.interpret(question)
        chunks = self.store.query(
            question,
            category=filters.category,
            published_after=filters.published_after,
            limit=max(self.retrieval_limit * 3, self.retrieval_limit),
        )
        chunks = _rerank(
            question,
            chunks,
            now=self.interpreter.clock(),
            minimum_relevance=relevance_threshold,
        )[: self.retrieval_limit]
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


def _rerank(
    question: str,
    chunks: list[ArticleChunk],
    now: datetime,
    minimum_relevance: float = 0.5,
) -> list[ArticleChunk]:
    """Prefer query-relevant evidence while giving recent news a bounded boost."""
    if not chunks:
        return []
    scored: list[tuple[float, ArticleChunk]] = []
    for chunk in chunks:
        relevance = _term_overlap(question, f"{chunk.metadata.get('title', '')} {chunk.text}")
        if relevance < minimum_relevance:
            continue
        age_days = max(0.0, (now - chunk.published_at).total_seconds() / 86400)
        recency = 1.0 / (1.0 + age_days)
        scored.append((0.9 * relevance + 0.1 * recency, chunk))
    scored.sort(key=lambda item: (item[0], item[1].published_at.timestamp()), reverse=True)
    return [chunk for _, chunk in scored]


def _term_overlap(query: str, document: str) -> float:
    stopwords = {
        "a", "about", "after", "and", "bullet", "bullets", "did", "for", "in", "is", "latest",
        "news", "of", "points", "since", "summarize", "summary", "the", "today", "what", "why",
    }
    query_terms = {
        term for term in re.findall(r"[a-z0-9]+", query.casefold())
        if term not in stopwords and not term.isdigit()
    }
    document_terms = set(re.findall(r"[a-z0-9]+", document.casefold()))
    if "stock" in query_terms:
        query_terms.add("stocks")
        query_terms.remove("stock")
    if not query_terms:
        return 1.0
    return len(query_terms & document_terms) / len(query_terms)
