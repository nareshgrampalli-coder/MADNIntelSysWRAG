from datetime import timezone

from news_rag.ingestion import (
    FeedSource,
    FinanceFetcher,
    RssSourceAdapter,
    StocksFetcher,
    deduplicate_articles,
    parse_rss,
)
from news_rag.models import NewsCategory
from news_rag.sources import sources_for


RSS = b"""
<rss><channel>
  <item>
    <title>Markets react to policy news</title>
    <link>https://example.com/one</link>
    <description>Markets moved after the announcement.</description>
    <pubDate>Sat, 26 Sep 2026 08:00:00 GMT</pubDate>
  </item>
  <item>
    <title>Same story elsewhere</title>
    <link>https://example.com/two</link>
    <description>Markets moved after the announcement.</description>
    <pubDate>Sat, 26 Sep 2026 08:05:00 GMT</pubDate>
  </item>
</channel></rss>
"""


def test_parse_rss_normalizes_article_fields() -> None:
    source = FeedSource("Example Finance", "https://example.com/rss", NewsCategory.FINANCE)

    articles = parse_rss(RSS, source)

    assert len(articles) == 2
    assert articles[0].category is NewsCategory.FINANCE
    assert articles[0].published_at.tzinfo == timezone.utc
    assert articles[0].content == "Markets moved after the announcement."


def test_deduplicate_articles_removes_duplicate_content() -> None:
    source = FeedSource("Example", "https://example.com/rss", NewsCategory.FINANCE)
    articles = parse_rss(RSS, source)

    unique = deduplicate_articles(articles)

    assert len(unique) == 1
    assert unique[0].url == "https://example.com/one"


def test_domain_fetcher_continues_after_source_failure() -> None:
    class FakeAdapter:
        def fetch(self, source: FeedSource):
            if source.name == "Broken":
                raise OSError("network failure")
            return parse_rss(RSS, source)

    fetcher = FinanceFetcher(
        sources=(
            FeedSource("Broken", "https://bad.example/rss", NewsCategory.FINANCE),
            FeedSource("Working", "https://good.example/rss", NewsCategory.FINANCE),
        ),
        adapter=FakeAdapter(),
    )

    assert len(fetcher.fetch()) == 1


def test_domain_fetcher_applies_source_relevance_terms() -> None:
    class FakeAdapter:
        def fetch(self, source: FeedSource):
            return parse_rss(RSS, source)

    fetcher = FinanceFetcher(
        sources=(FeedSource("Finance", "https://example.com/rss", NewsCategory.FINANCE, ("markets",)),),
        adapter=FakeAdapter(),
    )

    assert len(fetcher.fetch()) == 1


def test_stocks_fetcher_uses_stocks_category() -> None:
    source = FeedSource("India Stocks", "https://example.com/rss", NewsCategory.STOCKS, ("nifty",))

    class FakeAdapter:
        def fetch(self, feed_source: FeedSource):
            return parse_rss(RSS.replace(b"Markets react", b"Nifty reacts"), feed_source)

    articles = StocksFetcher((source,), adapter=FakeAdapter()).fetch()

    assert articles[0].category is NewsCategory.STOCKS


def test_adapter_retries_then_returns_payload() -> None:
    attempts = 0

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return RSS

    def opener(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("temporary failure")
        return Response()

    source = FeedSource("Example", "https://example.com/rss", NewsCategory.FINANCE)
    articles = RssSourceAdapter(opener=opener, retries=1).fetch(source)

    assert attempts == 2
    assert articles[0].title == "Markets react to policy news"


def test_default_sources_exist_for_each_domain() -> None:
    for category in NewsCategory:
        sources = sources_for(category)

        assert sources
        assert all(source.category is category for source in sources)


def test_default_sources_provide_multiple_queries_per_domain() -> None:
    for category in NewsCategory:
        assert len(sources_for(category)) >= 2
