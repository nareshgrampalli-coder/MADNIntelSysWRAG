"""Application-facing data preparation helpers."""

from datetime import datetime, timezone

from .models import NewsCategory, QueryResponse
from .query_engine import QueryEngine, QueryInterpreter
from .vector_store import VectorStore


def build_contextual_question(messages: list[dict[str, str]], question: str) -> str:
    """Keep referential follow-ups tied to the prior question only."""
    user_questions = [
        message["content"].strip().casefold()
        for message in messages[-6:]
        if message["role"] == "user"
    ]
    normalized_question = question.strip().casefold()
    if normalized_question in user_questions:
        return question
    if not _is_contextual_follow_up(normalized_question):
        return question
    previous_question = next(
        (message["content"].strip() for message in reversed(messages) if message["role"] == "user"),
        "",
    )
    return question if not previous_question else f"{previous_question} {question}"


def _is_contextual_follow_up(question: str) -> bool:
    return question.startswith((
        "what about ",
        "how about ",
        "what are the risks",
        "tell me more",
        "can you elaborate",
        "why is that",
        "how does that",
        "what does that",
    )) or question in {"why?", "how?", "and?"}


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
    engine = QueryEngine(store, interpreter=QueryInterpreter(clock=clock), retrieval_limit=3)
    briefing: list[tuple[NewsCategory, QueryResponse]] = []
    seen_urls: set[str] = set()
    for category in NewsCategory:
        topic = "stock market" if category is NewsCategory.STOCKS else category.value
        response = engine.answer(
            f"latest {topic} news today",
            relevance_threshold=0.0,
            distinct_articles=True,
        )
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


def retrieval_metrics(coverage: dict[NewsCategory, int]) -> dict[str, float | int]:
    """Summarize category retrieval coverage for the ingestion report."""
    category_count = len(coverage)
    covered_count = sum(count > 0 for count in coverage.values())
    total_sources = sum(coverage.values())
    return {
        "total_sources": total_sources,
        "covered_categories": covered_count,
        "category_count": category_count,
        "coverage_percent": round(covered_count / category_count * 100, 1) if category_count else 0.0,
    }


def verify_query_interpretation() -> dict[str, bool]:
    """Exercise category, date, and conversational query interpretation."""
    now = datetime(2026, 9, 27, 12, tzinfo=timezone.utc)
    interpreter = QueryInterpreter(clock=lambda: now)
    checks: dict[str, bool] = {}
    for category in NewsCategory:
        filters = interpreter.interpret(f"latest {category.value} news")
        checks[f"category:{category.value}"] = filters.category is category
    today = interpreter.interpret("latest news today")
    checks["date:today"] = today.published_after == datetime(2026, 9, 27, tzinfo=timezone.utc)
    follow_up = interpreter.interpret("what are the risks?")
    checks["follow-up:neutral"] = follow_up.category is None and follow_up.published_after is None
    repeated = interpreter.interpret("latest finance news")
    checks["repeated:stable"] = repeated.category is NewsCategory.FINANCE
    return checks


def verify_grounding_quality(store: VectorStore) -> dict[str, bool]:
    """Confirm supported questions cite evidence and unsupported ones refuse."""
    engine = QueryEngine(store, retrieval_limit=3)
    supported = engine.answer("latest news", relevance_threshold=0.0)
    unsupported = engine.answer("news about qzxvplm quorvex 8f41c", relevance_threshold=0.5)
    return {
        "supported:cited": supported.grounded and bool(supported.citations),
        "unsupported:refused": not unsupported.grounded and not unsupported.citations,
    }
