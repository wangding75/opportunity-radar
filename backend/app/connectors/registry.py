from __future__ import annotations

import json

from app.connectors.base import SourceConnector
from app.core.config import settings


class SourceRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, SourceConnector] = {}

    def register(self, connector: SourceConnector) -> None:
        source_id = connector.descriptor.source_id
        if source_id in self._connectors:
            raise ValueError(f"connector already registered: {source_id}")
        self._connectors[source_id] = connector

    def get(self, source_id: str) -> SourceConnector:
        try:
            return self._connectors[source_id]
        except KeyError as exc:
            raise KeyError(f"unknown source: {source_id}") from exc

    def list(self) -> list[SourceConnector]:
        return list(self._connectors.values())

    def close(self) -> None:
        errors: list[str] = []
        for source_id, connector in self._connectors.items():
            try:
                connector.close()
            except Exception as exc:
                errors.append(f"{source_id}: {exc}")
        if errors:
            raise RuntimeError("connector close failure(s): " + "; ".join(errors))


def build_default_registry() -> SourceRegistry:
    # Imports stay local so tests can construct isolated registries without eagerly
    # constructing HTTP clients for every production connector.
    from app.connectors.feed import ConfiguredFeedConnector, FeedConfig
    from app.connectors.github import GitHubSearchConnector
    from app.connectors.google_trends import GoogleTrendsRssConnector
    from app.connectors.instrumented_app import InstrumentedAppConnector

    registry = SourceRegistry()
    registry.register(GitHubSearchConnector())
    registry.register(GoogleTrendsRssConnector())
    registry.register(InstrumentedAppConnector())

    if settings.discovery_feeds_json:
        try:
            configured = json.loads(settings.discovery_feeds_json)
        except json.JSONDecodeError as exc:
            raise ValueError("DISCOVERY_FEEDS_JSON must be valid JSON") from exc
        if not isinstance(configured, list):
            raise ValueError("DISCOVERY_FEEDS_JSON must be a JSON array")
        for row in configured:
            if not isinstance(row, dict):
                raise ValueError("every DISCOVERY_FEEDS_JSON entry must be an object")
            official = row.get("official", False)
            if not isinstance(official, bool):
                raise ValueError("feed official must be a JSON boolean")
            interval = row.get("interval_minutes", 120)
            if isinstance(interval, bool) or not isinstance(interval, int):
                raise ValueError("feed interval_minutes must be an integer")
            config = FeedConfig(
                source_id=str(row.get("source_id", "")).strip(),
                display_name=str(row.get("display_name", "")).strip(),
                url=str(row.get("url", "")).strip(),
                interval_minutes=interval,
                official=official,
            )
            if not config.display_name:
                raise ValueError(f"feed display_name is required: {config.source_id}")
            registry.register(ConfiguredFeedConnector(config))
    return registry
