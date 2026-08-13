from __future__ import annotations

import json
import httpx
import time

from app.core.config import settings
from app.core.http_limits import read_limited_response
from app.domain.enums import AcquisitionMethod, AcquisitionRisk, Capability, EvidenceQuality, ItemType
from app.domain.schemas import CollectedRecord, CollectionResult, CollectorQuery, SourceDescriptor
from .base import ConnectorRateLimitError, SourceConnector


class GitHubSearchConnector(SourceConnector):
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=15.0)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    @property
    def descriptor(self) -> SourceDescriptor:
        return SourceDescriptor(
            source_id="github",
            display_name="GitHub Search",
            acquisition_method=AcquisitionMethod.OFFICIAL_API,
            evidence_quality=EvidenceQuality.A,
            acquisition_risk=AcquisitionRisk.R0,
            capabilities={Capability.SEARCH, Capability.REPOSITORY},
        )

    def collect(self, query: CollectorQuery) -> CollectionResult:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        with self._client.stream(
            "GET",
            "https://api.github.com/search/repositories",
            params={"q": query.query, "sort": "updated", "order": "desc", "per_page": query.limit},
            headers=headers,
        ) as response:
            remaining = response.headers.get("X-RateLimit-Remaining")
            if response.status_code == 429 or (response.status_code == 403 and remaining == "0"):
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    seconds = int(retry_after)
                else:
                    reset = response.headers.get("X-RateLimit-Reset")
                    seconds = max(60, int(reset) - int(time.time())) if reset and reset.isdigit() else 60
                raise ConnectorRateLimitError("GitHub API rate limit reached", retry_after_seconds=seconds)
            response.raise_for_status()
            content = read_limited_response(response, max_bytes=10_000_000, label="GitHub API response")
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("GitHub API returned non-object JSON")
        records = []
        for item in payload.get("items", [])[: query.limit]:
            records.append(
                CollectedRecord(
                    external_id=str(item.get("id")) if item.get("id") is not None else None,
                    item_type=ItemType.REPOSITORY,
                    title=item.get("full_name") or item.get("name") or "",
                    text=item.get("description") or "",
                    url=item.get("html_url"),
                    payload={
                        "language": item.get("language"),
                        "topics": item.get("topics", []),
                        "stargazers_count": item.get("stargazers_count", 0),
                        "forks_count": item.get("forks_count", 0),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                    },
                )
            )
        return CollectionResult(source_id=self.descriptor.source_id, query=query.query, records=records)
