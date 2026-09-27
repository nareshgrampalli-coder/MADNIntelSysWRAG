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
    text = line.strip()
    if len(text) <= limit:
        return text
    working = text.rstrip(". ")
    truncated = working[: limit + 1]
    boundary = max(truncated.rfind(". "), truncated.rfind("! "), truncated.rfind("? "))
    if boundary > limit // 2:
        return working[: boundary + 1]
    if text.endswith((".", "!", "?")):
        return text
    return re.sub(r"\s+\S*$", "", truncated).rstrip() + "..."


def format_chat_answer(answer: str) -> str:
    """Format an engine answer for chat display, preserving multi-category structure."""
    if answer.startswith("**") or "\n\n**" in answer:
        lines: list[str] = []
        for line in answer.splitlines():
            stripped = line.strip()
            if not stripped:
                lines.append("")
            elif stripped.startswith("**") and stripped.endswith("**"):
                lines.append(stripped)
            else:
                lines.append(f"- {trim_sentence(stripped.strip('- '))}")
        return "\n".join(lines).strip("\n")
    answer_lines = [line.strip("- ").strip() for line in answer.splitlines() if line.strip()]
    if len(answer_lines) < 3 and len(answer_lines) == 1:
        answer_lines = [part.strip() for part in answer.split(". ") if part.strip()]
    return "\n".join(f"- {trim_sentence(line)}" for line in answer_lines[:3])
