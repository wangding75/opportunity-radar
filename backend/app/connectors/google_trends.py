from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import httpx

from app.core.config import settings
from app.core.http_limits import read_limited_response
from app.core.time import as_utc_naive, utc_now
from app.domain.enums import (
    AcquisitionMethod,
    AcquisitionRisk,
    Capability,
    EvidenceQuality,
    ItemType,
    QueryMode,
)
from app.domain.schemas import CollectedRecord, CollectionResult, CollectorQuery, SourceDescriptor
from .base import ConnectorRateLimitError, ScheduledSourceQuery, SourceConnector

_TRENDS_NS = "https://trends.google.com/trending/rss"
_GEO_RE = re.compile(r"^[A-Za-z]{2}$")
_TRAFFIC_RE = re.compile(r"([\d,.]+)\s*([KMB]?)\+?", re.IGNORECASE)


def _parse_traffic(value: str | None) -> int | None:
    if not value:
        return None
    match = _TRAFFIC_RE.search(value.strip())
    if not match:
        return None
    number = float(match.group(1).replace(",", ""))
    multiplier = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[match.group(2).upper()]
    return int(number * multiplier)


def _parse_pub_date(value: str | None):
    if not value:
        return utc_now()
    try:
        return as_utc_naive(parsedate_to_datetime(value))
    except (TypeError, ValueError, OverflowError):
        return utc_now()


class GoogleTrendsRssConnector(SourceConnector):
    """Google Trends "Trending now" RSS export.

    The connector intentionally covers the official RSS export surface only. It is
    a region discovery feed, not keyword-interest-over-time API access.
    """

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=15.0, follow_redirects=False)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    @property
    def descriptor(self) -> SourceDescriptor:
        return SourceDescriptor(
            source_id="google_trends_rss",
            display_name="Google Trends Trending Now RSS",
            acquisition_method=AcquisitionMethod.OFFICIAL_EXPORT,
            evidence_quality=EvidenceQuality.B,
            acquisition_risk=AcquisitionRisk.R0,
            capabilities={Capability.TREND, Capability.RELATED_KEYWORD, Capability.DISCOVERY_FEED},
            query_mode=QueryMode.REGION,
        )

    def scheduled_queries(self) -> list[ScheduledSourceQuery]:
        queries: list[ScheduledSourceQuery] = []
        for geo in settings.google_trends_geos:
            if _GEO_RE.fullmatch(geo):
                queries.append(ScheduledSourceQuery(query=geo, intent="DISCOVERY", interval_minutes=60, priority=90.0))
        return queries

    def collect(self, query: CollectorQuery) -> CollectionResult:
        geo = query.query.strip().upper()
        if not _GEO_RE.fullmatch(geo):
            raise ValueError("Google Trends RSS query must be a 2-letter region code such as US or TW")
        with self._client.stream(
            "GET",
            "https://trends.google.com/trending/rss",
            params={"geo": geo},
            headers={"User-Agent": "OpportunityRadar/0.8 (+personal-research)"},
        ) as response:
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                seconds = int(retry_after) if retry_after and retry_after.isdigit() else 60
                raise ConnectorRateLimitError("Google Trends RSS rate limit reached", retry_after_seconds=seconds)
            response.raise_for_status()
            content = read_limited_response(response, max_bytes=5_000_000, label="Google Trends RSS response")
        if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
            raise ValueError("Google Trends RSS XML declarations/entities are not allowed")
        try:
            root = ET.fromstring(content)
        except ET.ParseError as exc:
            raise ValueError("Google Trends RSS returned invalid XML") from exc

        records: list[CollectedRecord] = []
        for item in root.findall("./channel/item")[: query.limit]:
            title = (item.findtext("title") or "").strip()
            if not title:
                continue
            pub_date = (item.findtext("pubDate") or "").strip()
            approx_traffic = item.findtext(f"{{{_TRENDS_NS}}}approx_traffic")
            picture_source = item.findtext(f"{{{_TRENDS_NS}}}picture_source")
            news_titles = [
                (node.findtext(f"{{{_TRENDS_NS}}}news_item_title") or "").strip()
                for node in item.findall(f"{{{_TRENDS_NS}}}news_item")
            ]
            news_titles = [value for value in news_titles if value][:10]
            text = " | ".join(news_titles)
            records.append(
                CollectedRecord(
                    external_id=hashlib.sha256(f"{geo}|{title.lower()}|{pub_date}".encode("utf-8")).hexdigest(),
                    item_type=ItemType.TREND,
                    title=title,
                    text=text,
                    url=f"https://trends.google.com/trending?geo={geo}",
                    observed_at=_parse_pub_date(pub_date),
                    payload={
                        "geo": geo,
                        "approx_traffic_label": approx_traffic,
                        "approx_traffic": _parse_traffic(approx_traffic),
                        "picture_source": picture_source,
                        "related_news_titles": news_titles,
                    },
                )
            )
        return CollectionResult(source_id=self.descriptor.source_id, query=geo, records=records)
