from __future__ import annotations

import httpx
import pytest

from app.connectors.feed import ConfiguredFeedConnector, FeedConfig
from app.domain.enums import EvidenceQuality, QueryMode
from app.domain.schemas import CollectorQuery


def test_configured_rss_feed_parses_and_strips_markup():
    xml = b'''<?xml version="1.0"?>
    <rss version="2.0"><channel><item>
      <guid>item-1</guid><title>New AI workflow</title>
      <link>https://example.com/item-1</link>
      <description><![CDATA[<p>Automation <b>tool</b> launched</p>]]></description>
      <pubDate>Wed, 12 Aug 2026 09:00:00 +0000</pubDate>
    </item></channel></rss>'''
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=xml)))
    connector = ConfiguredFeedConnector(
        FeedConfig(
            source_id="example_official_feed",
            display_name="Example Official Feed",
            url="https://example.com/feed.xml",
            official=True,
        ),
        client=client,
    )
    assert connector.descriptor.query_mode == QueryMode.SCHEDULED
    assert connector.descriptor.evidence_quality == EvidenceQuality.B
    result = connector.collect(CollectorQuery(query="feed", limit=10))
    assert len(result.records) == 1
    assert result.records[0].title == "New AI workflow"
    assert result.records[0].text == "Automation tool launched"
    assert result.records[0].observed_at.isoformat() == "2026-08-12T09:00:00"
    client.close()


def test_configured_atom_feed_parses_standard_fields():
    xml = b'''<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry><id>abc</id><title>Automation signal</title>
      <link rel="alternate" href="https://example.org/a" />
      <summary>New workflow demand</summary><updated>2026-08-12T10:00:00Z</updated></entry>
    </feed>'''
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=xml)))
    connector = ConfiguredFeedConnector(
        FeedConfig(source_id="example_atom", display_name="Example Atom", url="https://example.org/feed"),
        client=client,
    )
    result = connector.collect(CollectorQuery(query="feed"))
    assert result.records[0].url == "https://example.org/a"
    assert result.records[0].payload["format"] == "atom"
    client.close()


def test_feed_config_rejects_non_https_url():
    with pytest.raises(ValueError, match="HTTPS"):
        FeedConfig(source_id="bad_feed", display_name="Bad", url="http://example.com/feed")


def test_configured_feed_rejects_doctype_and_entity_declarations():
    xml = b'''<?xml version="1.0"?>\n<!DOCTYPE rss [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>\n<rss><channel><item><title>&xxe;</title></item></channel></rss>'''
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=xml)))
    connector = ConfiguredFeedConnector(
        FeedConfig(source_id="unsafe_xml_feed", display_name="Unsafe XML", url="https://example.org/feed"),
        client=client,
    )
    with pytest.raises(ValueError, match="declarations/entities"):
        connector.collect(CollectorQuery(query="feed"))
    client.close()
