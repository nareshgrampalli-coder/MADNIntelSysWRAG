"""Presentation helpers shared by the Streamlit interface."""

from datetime import date

from .models import NewsCategory, QueryResponse


def apply_filters(question: str, category: NewsCategory | None, start_date: date | None) -> str:
    additions: list[str] = []
    if category:
        additions.append(category.value)
    if start_date:
        additions.append(f"since {start_date.isoformat()}")
    return f"{question} ({', '.join(additions)})" if additions else question


def citation_lines(response: QueryResponse) -> list[str]:
    return [
        f"[{citation.title}]({citation.url}) - {citation.source}, {citation.published_at.date().isoformat()}"
        for citation in response.citations
    ]
