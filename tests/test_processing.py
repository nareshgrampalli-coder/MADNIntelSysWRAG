from datetime import datetime, timezone

import pytest

from news_rag.models import NewsCategory, RawArticle
from news_rag.processing import chunk_article, clean_text, process_article


ARTICLE = RawArticle(
    title="Markets and AI update",
    url="https://example.com/story",
    source="Example News",
    published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
    content=(
        "<nav>Navigation</nav><p>RBI announced a new policy rate. "
        "Markets reacted as technology companies gained.</p><script>tracking()</script>"
    ),
    category=NewsCategory.FINANCE,
)


def test_clean_text_removes_markup_and_ignored_sections() -> None:
    assert clean_text(ARTICLE.content) == "RBI announced a new policy rate. Markets reacted as technology companies gained."


def test_process_article_preserves_provenance_and_derives_metadata() -> None:
    processed = process_article(ARTICLE)

    assert processed.article.url == ARTICLE.url
    assert processed.article.published_at == ARTICLE.published_at
    assert "finance" in processed.tags
    assert "policy" in processed.tags
    assert "RBI" in processed.entities
    assert processed.summary.startswith("RBI announced")


def test_chunk_article_preserves_provenance_and_respects_limit() -> None:
    processed = process_article(ARTICLE)

    chunks = chunk_article(processed, max_words=5)

    assert len(chunks) > 1
    assert all(len(chunk.text.split()) <= 5 for chunk in chunks)
    assert all(chunk.article_url == ARTICLE.url for chunk in chunks)
    assert all(chunk.category is NewsCategory.FINANCE for chunk in chunks)
    assert chunks[0].metadata["title"] == ARTICLE.title


def test_chunk_article_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError):
        chunk_article(process_article(ARTICLE), max_words=0)
