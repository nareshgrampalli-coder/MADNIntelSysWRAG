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


def _is_summary_request(question: str) -> bool:
    return bool(re.search(r"\b(?:summari[sz]e|summary|overview|roundup)\b", question.casefold()))


def _is_headline_request(question: str) -> bool:
    normalized = question.casefold()
    if _is_summary_request(question) and any(category.value in normalized for category in NewsCategory):
        return False
    return bool(
        re.search(r"\bheadlines?\b", normalized)
        or re.search(r"\bwhat happened\b", normalized)
        or re.search(r"\b(?:today|latest|recent)\b.*\bnews\b", normalized)
        or _is_summary_request(question) and re.search(r"\b(?:today|latest|recent)\b", normalized)
    )


def _requests_certain_future(question: str) -> bool:
    normalized = question.casefold()
    certainty = re.search(r"\b(?:definitely|certainly|guaranteed|for sure|without fail)\b", normalized)
    future = re.search(r"\b(?:will|happen|future|next month|next year)\b", normalized)
    return bool(certainty and future)


def _headline_matches_category(chunk: ArticleChunk, category: NewsCategory) -> bool:
    topic_terms = {
        NewsCategory.TECHNOLOGY: ("technology", "tech", "software", "artificial intelligence", "cyber", "chip", "gadget"),
        NewsCategory.FINANCE: ("finance", "financial", "money", "insurance", "tax", "salary", "bank", "rbi", "investment", "market", "stock", "nre"),
        NewsCategory.POLITICS: ("politic", "government", "minister", "parliament", "election", "vote", "diplomat", "diplomacy", "policy", "bjp"),
        NewsCategory.STOCKS: ("stock", "market", "nifty", "sensex", "share", "investor", "investment"),
        NewsCategory.SPORTS: ("sport", "game", "athlete", "player", "match", "tournament", "medal", "badminton", "cricket"),
    }
    title = chunk.metadata.get("title", "").casefold()
    return any(term in title for term in topic_terms[category])


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
            title = _clean_excerpt(chunk.metadata.get("title", ""))
            headline_request = _is_headline_request(question)
            using_title_fallback = headline_request
            if headline_request:
                text = title
            else:
                text = chunk.metadata.get("summary", "") if _is_summary_request(question) else ""
            text = _clean_excerpt(text) if text else ""
            if text and (len(text) > 600 or len(text) < 40 and _is_summary_request(question)):
                text = title
                using_title_fallback = True
            if text and title and not using_title_fallback:
                text = re.sub(rf"^{re.escape(title)}[\s|:.-]*", "", text, flags=re.IGNORECASE)
            if using_title_fallback and (len(title) < 20 or title.casefold() in {"stock market news", "today news", "news"}):
                continue
            if not text:
                text = _clean_excerpt(chunk.text)
            sentences = [text] if using_title_fallback else re.split(r"(?<=[.!?])\s+", text)
            for sentence in sentences:
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
        "a", "about", "an", "and", "are", "be", "been", "but", "bullet", "bullets", "can", "certainly",
        "did", "do", "does", "focus", "for", "from", "give", "guaranteed", "happen", "happened", "has", "have", "headline", "headlines", "how", "i",
        "in", "is", "it", "latest", "me", "more", "news", "next", "of", "on", "or", "overall", "please",
        "points", "recent", "should", "since", "summarize", "summary", "tell", "than", "that", "the", "this", "top",
        "today", "todays", "was", "were", "what", "when", "which", "why", "will", "with", "without", "would",
        "you", "s",
    }
    normalized = question.casefold().replace("’", "'")
    normalized = re.sub(r"(?<=\w)'s\b", "", normalized)
    return {
        term for term in re.findall(r"[a-z0-9]+", normalized)
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

    def answer(
        self,
        question: str,
        relevance_threshold: float = 0.5,
        distinct_articles: bool = False,
    ) -> QueryResponse:
        if _requests_each_category(question):
            return self._answer_each_category()
        if _requests_certain_future(question):
            return QueryResponse(
                answer="I can't determine what will definitely happen. I can summarize reported forecasts, but they remain uncertain."
            )
        distinct_articles = distinct_articles or _is_summary_request(question) or _is_headline_request(question)
        filters = self.interpreter.interpret(question)
        minimum_relevance = relevance_threshold
        if (_is_summary_request(question) or _is_headline_request(question)) and filters.category:
            broad_terms = {filters.category.value.casefold(), "stock", "stocks", "market", "markets"}
            if _summary_terms(question) <= broad_terms:
                minimum_relevance = 0.0
        candidate_limit = (
            self.store.count()
            if distinct_articles
            else max(self.retrieval_limit * 3, self.retrieval_limit)
        )
        chunks = self.store.query(
            question,
            category=filters.category,
            published_after=filters.published_after,
            limit=candidate_limit,
        )
        if _is_headline_request(question) and filters.category:
            chunks = [chunk for chunk in chunks if _headline_matches_category(chunk, filters.category)]
        chunks = _rerank(
            question,
            chunks,
            now=self.interpreter.clock(),
            minimum_relevance=minimum_relevance,
        )
        if _requests_single_article(question):
            focused_chunks = _focus_article_chunks(question, chunks)
            if focused_chunks:
                chunks = focused_chunks
        else:
            focused_chunks = _focus_topic_chunks(question, chunks)
            if focused_chunks:
                chunks = focused_chunks
        if distinct_articles:
            chunks = _best_chunk_per_article(chunks)
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


def _best_chunk_per_article(chunks: list[ArticleChunk]) -> list[ArticleChunk]:
    best_chunks: dict[str, ArticleChunk] = {}
    for chunk in chunks:
        best_chunks.setdefault(chunk.article_url, chunk)
    return list(best_chunks.values())


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
    if matching:
        return matching
    if any(term in terms for term in {"tomorrow", "forecast", "prediction", "outlook", "expected"}):
        article_scores: dict[str, tuple[int, list[ArticleChunk]]] = {}
        for chunk in chunks:
            title_terms = set(re.findall(r"[a-z0-9]+", chunk.metadata.get("title", "").casefold()))
            score, article_chunks = article_scores.setdefault(chunk.article_url, (len(terms & title_terms), []))
            article_scores[chunk.article_url] = (score, [*article_chunks, chunk])
        if article_scores:
            score, focused = max(article_scores.values(), key=lambda item: item[0])
            if score >= 2:
                return focused
    return chunks


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
    query_terms = _summary_terms(query)
    document_terms = set(re.findall(r"[a-z0-9]+", document.casefold()))
    if "stock" in query_terms:
        query_terms.add("stocks")
        query_terms.remove("stock")
    if not query_terms:
        return 1.0
    return len(query_terms & document_terms) / len(query_terms)
