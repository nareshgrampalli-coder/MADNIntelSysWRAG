from datetime import datetime, timezone

from news_rag.ingestion import DomainFetcher
from news_rag.models import NewsCategory, RawArticle
from news_rag.orchestration import NewsPipeline
from news_rag.vector_store import JsonVectorStore


class FakeFetcher(DomainFetcher):
    def __init__(self, articles=None, error: Exception | None = None):
        self.articles = articles or []
        self.error = error

    def fetch(self):
        if self.error:
            raise self.error
        return self.articles


def article() -> RawArticle:
    return RawArticle(
        title="Policy update",
        url="https://example.com/policy",
        source="Example News",
        published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
        content="RBI announced a new policy rate for markets.",
        category=NewsCategory.FINANCE,
    )


def test_pipeline_runs_fetch_process_and_store(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    report = NewsPipeline([FakeFetcher([article()])], store).run_once()

    assert report.succeeded
    assert report.articles_fetched == 1
    assert report.chunks_stored == 1
    assert store.count() == 1


def test_pipeline_isolates_fetcher_failures(tmp_path) -> None:
    store = JsonVectorStore(tmp_path / "vectors.json")
    pipeline = NewsPipeline([FakeFetcher(error=OSError("feed unavailable")), FakeFetcher([article()])], store)

    report = pipeline.run_once()

    assert not report.succeeded
    assert "feed unavailable" in report.errors[0]
    assert report.articles_fetched == 1
    assert store.count() == 1
