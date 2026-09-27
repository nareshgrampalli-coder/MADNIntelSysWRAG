from datetime import datetime, timezone
from urllib.error import HTTPError

from news_rag.ingestion import (
    FeedSource,
    FinanceFetcher,
    RssSourceAdapter,
    StocksFetcher,
    deduplicate_articles,
    parse_rss,
)
from news_rag.models import NewsCategory, RawArticle
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
    assert fetcher.errors == ["Broken: failed to fetch https://bad.example/rss"]


def test_domain_fetcher_applies_source_relevance_terms() -> None:
    class FakeAdapter:
        def fetch(self, source: FeedSource):
            return parse_rss(RSS, source)

    fetcher = FinanceFetcher(
        sources=(FeedSource("Finance", "https://example.com/rss", NewsCategory.FINANCE, ("markets",)),),
        adapter=FakeAdapter(),
    )

    assert len(fetcher.fetch()) == 1


def test_domain_fetcher_fills_three_article_category_quota_across_feeds() -> None:
    sources = (
        FeedSource("Finance one", "https://example.com/one", NewsCategory.FINANCE),
        FeedSource("Finance two", "https://example.com/two", NewsCategory.FINANCE),
    )

    class FakeAdapter:
        def fetch(self, source: FeedSource):
            offset = 0 if source.name == "Finance one" else 2
            return [
                RawArticle(
                    title=f"India finance story {index}",
                    url=f"https://example.com/{index}",
                    source=source.name,
                    published_at=datetime(2026, 9, 26, index, tzinfo=timezone.utc),
                    content=f"Indian markets and finance update {index}.",
                    category=source.category,
                    summary="Indian finance update.",
                )
                for index in range(offset + 1, offset + 3)
            ]

    articles = FinanceFetcher(sources=sources, adapter=FakeAdapter()).fetch()

    assert len(articles) == 3
    assert [article.title for article in articles] == [
        "India finance story 4",
        "India finance story 3",
        "India finance story 2",
    ]


def test_domain_fetcher_looks_past_irrelevant_leading_feed_items() -> None:
    payload = b"""<rss><channel>
      <item><title>Global update one</title><link>https://example.com/1</link><description>Global markets update.</description><pubDate>Sat, 26 Sep 2026 08:00:00 GMT</pubDate></item>
      <item><title>Global update two</title><link>https://example.com/2</link><description>Global markets update.</description><pubDate>Sat, 26 Sep 2026 08:01:00 GMT</pubDate></item>
      <item><title>Global update three</title><link>https://example.com/3</link><description>Global markets update.</description><pubDate>Sat, 26 Sep 2026 08:02:00 GMT</pubDate></item>
      <item><title>India markets update</title><link>https://example.com/4</link><description>Indian markets update.</description><pubDate>Sat, 26 Sep 2026 08:03:00 GMT</pubDate></item>
    </channel></rss>"""

    class FakeAdapter:
        def fetch(self, source: FeedSource):
            return parse_rss(payload, source)

    fetcher = FinanceFetcher(
        sources=(FeedSource("Finance", "https://example.com/rss", NewsCategory.FINANCE, ("markets",)),),
        adapter=FakeAdapter(),
    )

    assert [article.title for article in fetcher.fetch()] == ["India markets update"]


def test_domain_fetcher_rejects_foreign_story_with_incidental_india_body_text() -> None:
    source = FeedSource("News", "https://example.com/rss", NewsCategory.FINANCE)

    class FakeAdapter:
        def fetch(self, feed_source: FeedSource):
            return [
                RawArticle(
                    title="One dead, hundreds of flights cancelled, power lines hit as 'Nor'easter' storm batters parts of US: What we know so far",
                    url="https://example.com/storm",
                    source=feed_source.name,
                    published_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
                    content="US storm causes widespread disruption. India was mentioned in unrelated page content.",
                    category=feed_source.category,
                    summary="US storm causes widespread disruption.",
                )
            ]

    fetcher = FinanceFetcher(sources=(source,), adapter=FakeAdapter())

    assert fetcher.fetch() == []


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

    assert attempts == 3
    assert articles[0].title == "Markets react to policy news"


def test_adapter_revalidates_cached_response_with_etag(tmp_path) -> None:
    source = FeedSource("Example", "https://example.com/rss", NewsCategory.FINANCE)
    calls = 0

    class Headers:
        def get(self, name):
            return "\"v1\"" if name == "ETag" else None

    class Response:
        headers = Headers()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return RSS

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            return Response()
        assert request.headers["If-none-match"] == '"v1"'
        raise HTTPError(request.full_url, 304, "Not Modified", {}, None)

    adapter = RssSourceAdapter(opener=opener, retries=0, cache_dir=tmp_path)

    first = adapter._download(source.url)
    second = adapter._download(source.url)

    assert first == second == RSS
    assert calls == 2


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
