import httpx

from app.connectors.google_trends import GoogleTrendsRssConnector
from app.domain.enums import QueryMode
from app.domain.schemas import CollectorQuery


def test_google_trends_rss_parses_official_export_shape():
    xml = b'''<?xml version="1.0" encoding="UTF-8"?>
    <rss xmlns:ht="https://trends.google.com/trending/rss" version="2.0">
      <channel>
        <title>Daily Search Trends</title>
        <item>
          <title>ai video automation</title>
          <ht:approx_traffic>50K+</ht:approx_traffic>
          <pubDate>Wed, 12 Aug 2026 01:00:00 -0700</pubDate>
          <ht:picture_source>Example</ht:picture_source>
          <ht:news_item><ht:news_item_title>AI video tools surge</ht:news_item_title></ht:news_item>
        </item>
      </channel>
    </rss>'''

    def handler(request: httpx.Request):
        assert request.url.path == "/trending/rss"
        assert request.url.params["geo"] == "US"
        return httpx.Response(200, content=xml, headers={"content-type": "application/rss+xml"})

    connector = GoogleTrendsRssConnector(client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert connector.descriptor.query_mode == QueryMode.REGION
    result = connector.collect(CollectorQuery(query="us", limit=10))
    assert result.source_id == "google_trends_rss"
    assert result.query == "US"
    assert len(result.records) == 1
    record = result.records[0]
    assert record.title == "ai video automation"
    assert record.payload["approx_traffic"] == 50_000
    assert record.payload["related_news_titles"] == ["AI video tools surge"]
    assert record.observed_at.isoformat() == "2026-08-12T08:00:00"


def test_google_trends_rss_rejects_keyword_query():
    connector = GoogleTrendsRssConnector(client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(500))))
    try:
        connector.collect(CollectorQuery(query="ai video"))
    except ValueError as exc:
        assert "2-letter region code" in str(exc)
    else:
        raise AssertionError("expected invalid region to be rejected before network access")


def test_google_trends_connector_exposes_configured_region_schedules():
    connector = GoogleTrendsRssConnector(client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(500))))
    scheduled = connector.scheduled_queries()
    assert {row.query for row in scheduled} >= {"US", "TW"}
    assert all(row.intent == "DISCOVERY" for row in scheduled)
    assert all(row.interval_minutes == 60 for row in scheduled)


def test_google_trends_rss_surfaces_rate_limit_retry_window():
    from app.connectors.base import ConnectorRateLimitError

    connector = GoogleTrendsRssConnector(
        client=httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(429, headers={"Retry-After": "90"}))
        )
    )
    try:
        connector.collect(CollectorQuery(query="US", limit=1))
    except ConnectorRateLimitError as exc:
        assert exc.retry_after_seconds == 90
    else:
        raise AssertionError("expected rate limit exception")


def test_google_trends_rejects_doctype_entity_xml():
    import pytest
    xml = b'''<?xml version="1.0"?><!DOCTYPE rss [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><rss><channel><item><title>&xxe;</title></item></channel></rss>'''
    connector = GoogleTrendsRssConnector(
        client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=xml)))
    )
    with pytest.raises(ValueError, match="declarations/entities"):
        connector.collect(CollectorQuery(query="US"))
