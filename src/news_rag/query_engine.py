"""Date-aware, citation-preserving RAG query orchestration."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

from .ingestion import NOISE_PHRASES
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
            published_after = now.replace(hour=0, minute=0, second=0, microsecond=0)
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
        query_terms = _summary_terms(question)
        candidates: list[tuple[float, int, str]] = []
        seen: set[str] = set()
        order = 0
        for chunk in chunks:
            text = _clean_excerpt(chunk.text)
            for sentence in re.split(r"(?<=[.!?])\s+", text):
                sentence = sentence.strip(" -")
                key = sentence.casefold()
                if len(sentence) < 15 or key in seen:
                    continue
                seen.add(key)
                sentence_terms = set(re.findall(r"[a-z0-9]+", key))
                relevance = len(query_terms & sentence_terms) / max(1, len(query_terms))
                candidates.append((relevance, order, sentence.rstrip(".!?") + "."))
                order += 1
        candidates.sort(key=lambda item: (-item[0], item[1]))
        excerpts = [sentence for _, _, sentence in candidates[:3]]
        if not excerpts:
            excerpts = [_clean_excerpt(chunks[0].text).rstrip(".!?") + "."]
        return "\n".join(f"- {excerpt}" for excerpt in excerpts)


def _clean_excerpt(value: str) -> str:
    text = " ".join(value.split())
    for phrase in NOISE_PHRASES:
        text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:Get Latest|View Market Dashboard|Read more)\b.*", "", text, flags=re.IGNORECASE)
    return " ".join(text.split())


def _summary_terms(question: str) -> set[str]:
    stopwords = {
        "a", "about", "an", "and", "are", "can", "did", "for", "give", "how", "in", "is", "me",
        "more", "news", "of", "on", "please", "recent", "summarize", "tell", "the", "this", "today",
        "what", "when", "which", "why", "with", "you",
    }
    return {
        term for term in re.findall(r"[a-z0-9]+", question.casefold())
        if term not in stopwords and not term.isdigit()
    }


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
        if _requests_each_category(question):
            return self._answer_each_category()
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
        )
        if _requests_single_article(question):
            focused_chunks = _focus_article_chunks(question, chunks)
            if focused_chunks:
                chunks = focused_chunks
        else:
            focused_chunks = _focus_topic_chunks(question, chunks)
            if focused_chunks:
                chunks = focused_chunks
        chunks = chunks[: self.retrieval_limit]
        if not chunks:
            return QueryResponse(answer="I don't have news on that.")
        citations = _citations(chunks)
        return QueryResponse(
            answer=self.generator.generate(question, chunks),
            citations=tuple(citations),
            grounded=True,
        )

    def _answer_each_category(self) -> QueryResponse:
        answers: list[str] = []
        citations: list[SourceCitation] = []
        seen_urls: set[str] = set()
        for category in NewsCategory:
            topic = "stock market" if category is NewsCategory.STOCKS else category.value
            response = self.answer(f"Summarize latest {topic} news in 3 bullet points", relevance_threshold=0.0)
            if not response.grounded:
                continue
            answers.append(f"**{category.value.title()}**\n{response.answer}")
            for citation in response.citations:
                if citation.url not in seen_urls:
                    citations.append(citation)
                    seen_urls.add(citation.url)
        if not answers:
            return QueryResponse(answer="I don't have news on that.")
        return QueryResponse(answer="\n\n".join(answers), citations=tuple(citations), grounded=True)


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
                summary=chunk.metadata.get("summary", chunk.text),
            )
        )
    return citations


def _requests_each_category(question: str) -> bool:
    normalized = question.casefold()
    return "each categor" in normalized or "every categor" in normalized


def _requests_single_article(question: str) -> bool:
    normalized = question.casefold()
    return bool(re.search(r"\b(?:what is|what's|tell me about|explain)\b.*\barticle\b", normalized))


def _focus_article_chunks(question: str, chunks: list[ArticleChunk]) -> list[ArticleChunk]:
    query_terms = _summary_terms(question) - {"article"}
    if not query_terms:
        return chunks
    title_matches = [
        chunk
        for chunk in chunks
        if len(query_terms & set(re.findall(r"[a-z0-9]+", chunk.metadata.get("title", "").casefold()))) >= 2
    ]
    return title_matches or chunks


def _focus_topic_chunks(question: str, chunks: list[ArticleChunk]) -> list[ArticleChunk]:
    """Prefer evidence containing all significant terms of a multi-word topic."""
    terms = _summary_terms(question)
    if len(terms) < 2:
        return chunks
    matching = [
        chunk
        for chunk in chunks
        if terms <= set(
            re.findall(
                r"[a-z0-9]+",
                f"{chunk.metadata.get('title', '')} {chunk.text}".casefold(),
            )
        )
    ]
    return matching or chunks


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
        "a", "about", "after", "and", "ask", "bullet", "bullets", "can", "did", "for", "give", "in", "is",
        "i", "in", "latest", "me", "news", "of", "on", "overall", "points", "recent", "since",
        "summarize", "summary", "tell", "todays", "you",
        "the", "today", "what", "which", "why", "should", "focus",
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
