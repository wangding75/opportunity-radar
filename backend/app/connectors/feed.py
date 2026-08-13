from __future__ import annotations

import hashlib
import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import httpx

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

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class FeedConfig:
    source_id: str
    display_name: str
    url: str
    interval_minutes: int = 120
    official: bool = False

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{1,98}[a-z0-9]", self.source_id):
            raise ValueError(f"invalid feed source_id: {self.source_id}")
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError(f"feed URL must be HTTPS with a hostname: {self.url}")
        if not 15 <= self.interval_minutes <= 24 * 60:
            raise ValueError("feed interval_minutes must be between 15 and 1440")


def _clean_text(value: str | None, *, limit: int) -> str:
    if not value:
        return ""
    value = html.unescape(_TAG_RE.sub(" ", value))
    return _SPACE_RE.sub(" ", value).strip()[:limit]




def _safe_http_url(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    parsed = urlparse(value.strip())
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        return value.strip()[:10_000]
    return fallback


def _parse_datetime(value: str | None):
    if not value:
        return utc_now()
    raw = value.strip()
    try:
        return as_utc_naive(parsedate_to_datetime(raw))
    except (TypeError, ValueError, OverflowError):
        # Fall through to the ISO-8601 parser for providers that emit a
        # non-RFC date string; an invalid first format is not success.
        parsed = None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return as_utc_naive(parsed)
    except (TypeError, ValueError, OverflowError):
        return utc_now()


def _child_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for child in list(node):
        local = child.tag.rsplit("}", 1)[-1].lower()
        if local in names and child.text:
            return child.text.strip()
    return ""


def _atom_link(node: ET.Element) -> str:
    for child in list(node):
        if child.tag.rsplit("}", 1)[-1].lower() != "link":
            continue
        href = (child.attrib.get("href") or "").strip()
        rel = (child.attrib.get("rel") or "alternate").strip().lower()
        if href and rel in {"alternate", ""}:
            return href
    return ""


class ConfiguredFeedConnector(SourceConnector):
    """Scheduled RSS/Atom connector for explicitly configured public HTTPS feeds."""

    def __init__(self, config: FeedConfig, client: httpx.Client | None = None) -> None:
        self.config = config
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=15.0, follow_redirects=False)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    @property
    def descriptor(self) -> SourceDescriptor:
        return SourceDescriptor(
            source_id=self.config.source_id,
            display_name=self.config.display_name,
            acquisition_method=AcquisitionMethod.OFFICIAL_EXPORT if self.config.official else AcquisitionMethod.PUBLIC_WEB,
            evidence_quality=EvidenceQuality.B if self.config.official else EvidenceQuality.D,
            acquisition_risk=AcquisitionRisk.R0 if self.config.official else AcquisitionRisk.R1,
            capabilities={Capability.DISCOVERY_FEED, Capability.RELATED_KEYWORD},
            query_mode=QueryMode.SCHEDULED,
        )

    def scheduled_queries(self) -> list[ScheduledSourceQuery]:
        return [
            ScheduledSourceQuery(
                query="feed",
                intent="DISCOVERY",
                interval_minutes=self.config.interval_minutes,
                priority=75.0,
            )
        ]

    def collect(self, query: CollectorQuery) -> CollectionResult:
        if query.query != "feed":
            raise ValueError("configured feed connector only accepts its scheduled 'feed' query")
        with self._client.stream(
            "GET",
            self.config.url,
            headers={"User-Agent": "OpportunityRadar/0.8 (+personal-research)"},
        ) as response:
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                seconds = int(retry_after) if retry_after and retry_after.isdigit() else 60
                raise ConnectorRateLimitError(
                    f"feed rate limit reached: {self.config.source_id}",
                    retry_after_seconds=seconds,
                )
            response.raise_for_status()
            content = read_limited_response(response, max_bytes=5_000_000, label="feed response")
        if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
            raise ValueError("configured feed XML declarations/entities are not allowed")
        try:
            root = ET.fromstring(content)
        except ET.ParseError as exc:
            raise ValueError("configured feed returned invalid XML") from exc

        records: list[CollectedRecord] = []
        nodes = root.findall("./channel/item")
        atom_mode = False
        if not nodes:
            nodes = [node for node in list(root) if node.tag.rsplit("}", 1)[-1].lower() == "entry"]
            atom_mode = True

        for node in nodes[: query.limit]:
            title = _clean_text(_child_text(node, ("title",)), limit=20_000)
            if not title:
                continue
            link = _atom_link(node) if atom_mode else _child_text(node, ("link",))
            description = _child_text(node, ("summary", "description", "content"))
            published = _child_text(node, ("published", "updated", "pubdate"))
            guid = _child_text(node, ("id", "guid"))
            external_basis = guid or link or f"{title}|{published}"
            records.append(
                CollectedRecord(
                    external_id=hashlib.sha256(
                        f"{self.config.source_id}|{external_basis}".encode("utf-8")
                    ).hexdigest(),
                    item_type=ItemType.CONTENT,
                    title=title,
                    text=_clean_text(description, limit=50_000),
                    url=_safe_http_url(link, self.config.url),
                    observed_at=_parse_datetime(published),
                    payload={
                        "feed_url": self.config.url,
                        "official_feed": self.config.official,
                        "format": "atom" if atom_mode else "rss",
                    },
                )
            )
        return CollectionResult(source_id=self.config.source_id, query="feed", records=records)
