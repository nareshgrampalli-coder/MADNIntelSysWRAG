"""Presentation helpers shared by the Streamlit interface."""

from datetime import date
import re

from .models import NewsCategory, QueryResponse


def category_label(category: NewsCategory) -> str:
    return "Stocks Market" if category is NewsCategory.STOCKS else category.value.title()


def apply_filters(question: str, category: NewsCategory | None, start_date: date | None) -> str:
    additions: list[str] = []
    if category:
        additions.append(category.value)
    if start_date:
        additions.append(f"since {start_date.isoformat()}")
    return f"{question} ({', '.join(additions)})" if additions else question


def citation_lines(response: QueryResponse) -> list[str]:
    return [
        f"[{citation.title}]({citation.url}) - {citation.source}, {citation.published_at.strftime('%d-%b-%Y')}"
        for citation in response.citations
    ]


def trim_sentence(line: str, limit: int = 240) -> str:
    """Trim a summary line at a sentence boundary when it exceeds the limit."""
    text = line.rstrip(". ").strip()
    if len(text) <= limit:
        return text
    truncated = text[: limit + 1]
    boundary = max(truncated.rfind(". "), truncated.rfind("! "), truncated.rfind("? "))
    if boundary > limit // 2:
        return text[:boundary]
    return re.sub(r"\s+\S*$", "", truncated).rstrip() + "..."
