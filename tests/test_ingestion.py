from datetime import datetime, timezone

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
    <description>Indian markets moved after the announcement.</description>
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
    assert articles[0].content == "Indian markets moved after the announcement."


def test_parse_rss_accepts_items_without_description() -> None:
    source = FeedSource("Example Finance", "https://example.com/rss", NewsCategory.FINANCE)
    payload = RSS.replace(
        b"<description>Indian markets moved after the announcement.</description>",
        b"",
        1,
    )

    articles = parse_rss(payload, source)

    assert len(articles) == 2
    assert articles[0].content == articles[0].title


def test_parse_rss_accepts_iso_publication_dates() -> None:
    source = FeedSource("Yahoo Finance", "https://finance.yahoo.com/rss/", NewsCategory.FINANCE)
    payload = RSS.replace(b"Sat, 26 Sep 2026 08:00:00 GMT", b"2026-09-26T08:00:00Z")

    articles = parse_rss(payload, source)

    assert articles[0].published_at == datetime(2026, 9, 26, 8, tzinfo=timezone.utc)


def test_deduplicate_articles_removes_duplicate_content() -> None:
    source = FeedSource("Example", "https://example.com/rss", NewsCategory.FINANCE)
    articles = parse_rss(
        RSS.replace(
            b"<description>Markets moved after the announcement.</description>",
            b"<description>Indian markets moved after the announcement.</description>",
        ),
        source,
    )

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

    assert attempts == 4
    assert articles[0].title == "Markets react to policy news"


def test_adapter_fetches_article_content_from_links() -> None:
    source = FeedSource("Example", "https://example.com/rss", NewsCategory.FINANCE)
    html = b"<html><nav>Menu</nav><article>Full article body from the link.</article></html>"

    class Response:
        def __init__(self, payload: bytes):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return self.payload

    def opener(request, timeout):
        return Response(RSS if request.full_url.endswith("/rss") else html)

    articles = RssSourceAdapter(opener=opener, retries=0).fetch(source)

    assert articles[0].content == "Full article body from the link."


def test_adapter_removes_publisher_session_boilerplate() -> None:
    source = FeedSource("Example", "https://example.com/rss", NewsCategory.FINANCE)
    html = b"<article>Article body. You are logged in Loading LOGOUT You don't have any Active Subscription</article>"

    class Response:
        def __init__(self, payload: bytes):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return self.payload

    def opener(request, timeout):
        return Response(RSS if request.full_url.endswith("/rss") else html)

    articles = RssSourceAdapter(opener=opener, retries=0).fetch(source)

    assert articles[0].content == "Article body."


def test_adapter_removes_ad_and_promotion_containers() -> None:
    source = FeedSource("Example", "https://example.com/rss", NewsCategory.FINANCE)
    html = b"""
    <article>
      <p>Article body about the market outlook.</p>
      <div class='advertisement'>Sponsored broker promotion.</div>
      <div id='recommended-stories'>Read more related stories.</div>
      <p>Second relevant paragraph.</p>
    </article>
    """

    class Response:
        def __init__(self, payload: bytes):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return self.payload

    def opener(request, timeout):
        return Response(RSS if request.full_url.endswith("/rss") else html)

    articles = RssSourceAdapter(opener=opener, retries=0).fetch(source)

    assert articles[0].content == "Article body about the market outlook. Second relevant paragraph."


def test_default_sources_exist_for_each_domain(monkeypatch) -> None:
    monkeypatch.delenv("NEWS_RAG_FINANCE_RSS_URLS", raising=False)
    monkeypatch.delenv("NEWS_RAG_FINANCE_APPROVED_RSS_URLS", raising=False)

    for category in NewsCategory:
        sources = sources_for(category)

        assert sources
        assert all(source.category is category for source in sources)


def test_google_news_overrides_fall_back_to_publisher_defaults(monkeypatch) -> None:
    monkeypatch.setenv(
        "NEWS_RAG_FINANCE_RSS_URLS",
        "https://news.google.com/rss/search?q=finance",
    )

    sources = sources_for(NewsCategory.FINANCE)

    assert sources
    assert all("news.google.com" not in source.url for source in sources)


def test_default_sources_provide_multiple_queries_per_domain() -> None:
    for category in NewsCategory:
        assert sources_for(category)

    assert len(sources_for(NewsCategory.FINANCE)) == 2


def test_stocks_sources_use_only_livemint_markets() -> None:
    sources = sources_for(NewsCategory.STOCKS)

    assert len(sources) == 1
    assert sources[0].name == "LiveMint - Stocks"
    assert sources[0].url == "https://www.livemint.com/rss/markets"


def test_default_sources_use_requested_indian_publishers() -> None:
    urls = {source.url for category in NewsCategory for source in sources_for(category)}

    assert urls == {
        "https://finance.yahoo.com/rss/",
        "https://www.livemint.com/rss/news",
        "https://www.livemint.com/rss/money",
        "https://www.livemint.com/rss/politics",
        "https://www.livemint.com/rss/markets",
        "https://www.livemint.com/rss/sports",
    }
