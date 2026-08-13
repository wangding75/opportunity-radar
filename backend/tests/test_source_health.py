from __future__ import annotations

from app.connectors.base import SourceConnector
from app.connectors.registry import SourceRegistry
from app.db.session import SessionLocal
from app.domain.enums import AcquisitionMethod, AcquisitionRisk, Capability, EvidenceQuality, QueryMode
from app.domain.schemas import CollectorQuery, SourceDescriptor
from app.services.execution import execute_collection
from app.services.source_health import source_health_report


class AlwaysFailConnector(SourceConnector):
    def __init__(self):
        self.calls = 0

    @property
    def descriptor(self):
        return SourceDescriptor(
            source_id="always_fail",
            display_name="Always Fail",
            acquisition_method=AcquisitionMethod.OFFICIAL_API,
            evidence_quality=EvidenceQuality.A,
            acquisition_risk=AcquisitionRisk.R0,
            capabilities={Capability.SEARCH},
            query_mode=QueryMode.KEYWORD,
        )

    def collect(self, query: CollectorQuery):
        self.calls += 1
        raise RuntimeError("upstream unavailable")


def test_source_circuit_opens_after_three_failures_and_skips_fourth_call():
    connector = AlwaysFailConnector()
    registry = SourceRegistry()
    registry.register(connector)
    with SessionLocal() as db:
        for _ in range(3):
            try:
                execute_collection(db, registry, source_id="always_fail", query=CollectorQuery(query="test"))
            except RuntimeError:
                pass
        state = source_health_report(db, ["always_fail"])[0]
        assert state["status"] == "CIRCUIT_OPEN"
        assert state["consecutive_failures"] == 3
        assert state["circuit_open_until"] is not None

        result = execute_collection(db, registry, source_id="always_fail", query=CollectorQuery(query="test"))
        assert result["status"] == "SKIPPED"
        assert connector.calls == 3


def test_source_success_resets_failure_state():
    from app.domain.schemas import CollectedRecord, CollectionResult

    class RecoveringConnector(AlwaysFailConnector):
        def collect(self, query: CollectorQuery):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary outage")
            return CollectionResult(source_id="always_fail", query=query.query, records=[CollectedRecord(title="ok")])

    connector = RecoveringConnector()
    registry = SourceRegistry()
    registry.register(connector)
    with SessionLocal() as db:
        try:
            execute_collection(db, registry, source_id="always_fail", query=CollectorQuery(query="test"))
        except RuntimeError:
            pass
        result = execute_collection(db, registry, source_id="always_fail", query=CollectorQuery(query="test"))
        assert result["status"] == "SUCCEEDED"
        state = source_health_report(db, ["always_fail"])[0]
        assert state["status"] == "HEALTHY"
        assert state["consecutive_failures"] == 0
        assert state["last_error"] is None


def test_rate_limit_opens_circuit_immediately_and_tracks_metrics():
    from app.connectors.base import ConnectorRateLimitError

    class RateLimitedConnector(AlwaysFailConnector):
        @property
        def descriptor(self):
            base = super().descriptor
            return base.model_copy(update={"source_id": "rate_limited"})

        def collect(self, query: CollectorQuery):
            self.calls += 1
            raise ConnectorRateLimitError("quota reached", retry_after_seconds=120)

    connector = RateLimitedConnector()
    registry = SourceRegistry()
    registry.register(connector)
    with SessionLocal() as db:
        try:
            execute_collection(db, registry, source_id="rate_limited", query=CollectorQuery(query="test"))
        except ConnectorRateLimitError:
            pass
        state = source_health_report(db, ["rate_limited"])[0]
        assert state["status"] == "CIRCUIT_OPEN"
        assert state["rate_limited_runs"] == 1
        assert state["total_runs"] == 1
        assert state["failed_runs"] == 1
        assert state["last_duration_ms"] is not None
