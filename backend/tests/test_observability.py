from fastapi.testclient import TestClient

from app.core.observability import Metrics
from app.main import app
from app.services.provider_registry import FallbackProvider, ProviderCapability, ProviderRegistry, ProviderRouter


class _FailingProvider:
    def analyze(self, _payload):
        raise RuntimeError("synthetic provider failure")


class _WorkingProvider:
    def analyze(self, payload):
        return {"ok": True, "payload": payload}


def test_metrics_render_provider_calls_retries_fallbacks_selection_and_conflicts():
    metrics = Metrics()
    metrics.observe_provider_call("synthetic", "success")
    metrics.observe_provider_call("synthetic", "failure")
    metrics.observe_provider_retry("synthetic")
    metrics.observe_provider_fallback("synthetic", "heuristic")
    metrics.observe_provider_selection("majority", "heuristic")
    metrics.observe_provider_conflict("CONFLICT")
    output = metrics.render_prometheus()
    assert 'opportunity_radar_analysis_provider_calls_total{provider="synthetic",outcome="failure"} 1' in output
    assert 'opportunity_radar_analysis_provider_retries_total{provider="synthetic"} 1' in output
    assert 'opportunity_radar_analysis_provider_fallbacks_total{from_provider="synthetic",to_provider="heuristic"} 1' in output
    assert 'opportunity_radar_analysis_provider_selections_total{policy="majority",provider="heuristic"} 1' in output
    assert 'opportunity_radar_analysis_provider_conflicts_total{status="CONFLICT"} 1' in output


def test_fallback_lifecycle_is_visible_on_metrics_endpoint():
    registry = ProviderRegistry(unavailable_after_failures=5)
    registry.register("synthetic-failing", display_name="Synthetic failing", capabilities=["STRUCTURED_ANALYSIS"], factory=_FailingProvider)
    registry.register("synthetic-working", display_name="Synthetic working", capabilities=["STRUCTURED_ANALYSIS"], factory=_WorkingProvider)
    fallback = FallbackProvider(
        registry,
        ProviderRouter(registry, priority=["synthetic-failing", "synthetic-working"]),
        capability=ProviderCapability.STRUCTURED_ANALYSIS,
        retry_attempts=2,
        retry_backoff_seconds=0,
    )
    assert fallback.analyze({"data_class": "SYNTHETIC"})["ok"] is True
    output = TestClient(app).get("/metrics").text
    assert "opportunity_radar_analysis_provider_calls_total" in output
    assert 'provider="synthetic-failing",outcome="failure"' in output
    assert 'provider="synthetic-working",outcome="success"' in output
    assert 'from_provider="synthetic-failing",to_provider="synthetic-working"' in output
    assert 'provider="synthetic-failing"' in output and "retries_total" in output
