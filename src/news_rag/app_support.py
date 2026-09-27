"""Application-facing data preparation helpers."""

from datetime import datetime, timezone

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
        citations = sorted(
            (citation for citation in response.citations if citation.url not in seen_urls),
            key=lambda citation: citation.published_at,
            reverse=True,
        )
        citations = tuple(citations[:3])
        if not citations:
            continue
        seen_urls.update(citation.url for citation in citations)
        briefing.append((category, QueryResponse(answer=response.answer, citations=citations, grounded=True)))
    return briefing


def verify_retrieval_quality(store: VectorStore) -> dict[NewsCategory, int]:
    """Run one category query and return the number of retrieved citations."""
    engine = QueryEngine(store, retrieval_limit=3)
    coverage: dict[NewsCategory, int] = {}
    for category in NewsCategory:
        topic = "stock market" if category is NewsCategory.STOCKS else category.value
        response = engine.answer(f"latest {topic} news", relevance_threshold=0.0)
        coverage[category] = len(response.citations)
    return coverage
