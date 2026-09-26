"""Application-facing data preparation helpers."""

from datetime import datetime, timedelta, timezone

from .models import NewsCategory, QueryResponse
from .query_engine import QueryEngine, QueryInterpreter
from .vector_store import VectorStore


def build_sample_questions(store: VectorStore) -> dict[NewsCategory, tuple[str, ...]]:
    """Build distinct questions from indexed article titles."""
    questions: dict[NewsCategory, tuple[str, ...]] = {}
    for category in NewsCategory:
        chunks = store.query(category.value, category=category, limit=4)
        titles: list[str] = []
        for chunk in chunks:
            title = chunk.metadata.get("title", "").strip()
            if title and title not in titles:
                titles.append(title)
        questions[category] = tuple(f"What happened in {title}?" for title in titles[:3])
    return questions


def build_todays_briefing(
    store: VectorStore,
    now: datetime | None = None,
) -> list[tuple[NewsCategory, QueryResponse]]:
    """Build one grounded response per domain from the last 24 hours."""
    clock = lambda: now or datetime.now(timezone.utc)
    engine = QueryEngine(store, interpreter=QueryInterpreter(clock=clock), retrieval_limit=6)
    briefing: list[tuple[NewsCategory, QueryResponse]] = []
    seen_urls: set[str] = set()
    for category in NewsCategory:
        topic = "stock market" if category is NewsCategory.STOCKS else category.value
        response = engine.answer(f"latest {topic} news today", relevance_threshold=0.0)
        citations = [citation for citation in response.citations if citation.url not in seen_urls]
        if not citations:
            previous_day = (clock() - timedelta(days=1)).date()
            previous_response = engine.answer(f"latest {topic} news", relevance_threshold=0.0)
            citations = [
                citation
                for citation in previous_response.citations
                if citation.published_at.date() == previous_day and citation.url not in seen_urls
            ]
        citations = tuple(citations[:6])
        if not citations:
            continue
        seen_urls.update(citation.url for citation in citations)
        briefing.append((category, QueryResponse(answer=response.answer, citations=citations, grounded=True)))
    return briefing
