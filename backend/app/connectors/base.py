from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.schemas import CollectionResult, CollectorQuery, SourceDescriptor


class ConnectorRateLimitError(RuntimeError):
    def __init__(self, message: str, *, retry_after_seconds: int = 60) -> None:
        super().__init__(message)
        self.retry_after_seconds = max(1, int(retry_after_seconds))



@dataclass(frozen=True)
class ScheduledSourceQuery:
    query: str
    intent: str = "DISCOVERY"
    interval_minutes: int = 60
    priority: float = 80.0


class SourceConnector(ABC):
    @property
    @abstractmethod
    def descriptor(self) -> SourceDescriptor:
        raise NotImplementedError

    @abstractmethod
    def collect(self, query: CollectorQuery) -> CollectionResult:
        raise NotImplementedError

    def scheduled_queries(self) -> list[ScheduledSourceQuery]:
        """Connector-owned non-keyword discovery queries (regions, feeds, etc.)."""
        return []

    def close(self) -> None:
        """Release connector-owned resources."""

    def health(self) -> dict[str, str]:
        return {
            "status": "configured" if self.descriptor.enabled else "disabled",
            "source_id": self.descriptor.source_id,
            "query_mode": self.descriptor.query_mode.value,
        }
