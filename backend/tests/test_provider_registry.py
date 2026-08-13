from __future__ import annotations

import pytest
from types import SimpleNamespace

from app.services.provider_registry import (
    ProviderCapability,
    ProviderHealthStatus,
    ProviderNotFoundError,
    ProviderRegistry,
    ProviderRouter,
    FallbackProvider,
    EnsembleProvider,
)
from app.services.opportunity_analysis import OpportunityAnalysisResult
from app.services.provider_conflict import ProviderResultCandidate, select_provider_result


class FakeProvider:
    def __init__(self, fail: bool = False):
        self.fail = fail

    def analyze(self, payload):
        if self.fail:
            raise RuntimeError("provider outage")
        return {"ok": True, "payload": payload}


def test_registry_freezes_capabilities_and_reports_health():
    registry = ProviderRegistry(unavailable_after_failures=2)
    registry.register(
        "test",
        display_name="Test provider",
        capabilities=[ProviderCapability.STRUCTURED_ANALYSIS, "EVIDENCE_CITATION"],
        factory=FakeProvider,
    )
    descriptor = registry.descriptor("TEST")
    assert descriptor.supports(ProviderCapability.EVIDENCE_CITATION)
    tracked = registry.create_tracked("test")
    assert tracked.analyze({"id": 1})["ok"]
    health = registry.health("test")
    assert health.status == ProviderHealthStatus.HEALTHY
    assert health.successful_calls == 1
    assert registry.snapshot()[0]["capabilities"] == ["EVIDENCE_CITATION", "STRUCTURED_ANALYSIS"]


def test_registry_rejects_duplicates_and_unknown_provider():
    registry = ProviderRegistry()
    registry.register("test", display_name="Test", capabilities=[], factory=FakeProvider)
    with pytest.raises(ValueError, match="already registered"):
        registry.register("TEST", display_name="Duplicate", capabilities=[], factory=FakeProvider)
    with pytest.raises(ProviderNotFoundError):
        registry.create("missing")


def test_tracked_provider_marks_failure_and_unavailable_after_threshold():
    registry = ProviderRegistry(unavailable_after_failures=2)
    registry.register("test", display_name="Test", capabilities=[], factory=lambda: FakeProvider(fail=True))
    tracked = registry.create_tracked("test")
    for _ in range(2):
        with pytest.raises(RuntimeError, match="provider outage"):
            tracked.analyze(None)
    health = registry.health("test")
    assert health.status == ProviderHealthStatus.UNAVAILABLE
    assert health.failed_calls == 2
    assert health.last_error == "provider outage"


def test_router_selects_first_enabled_provider_matching_capability():
    registry = ProviderRegistry()
    registry.register("heuristic", display_name="Heuristic", capabilities=["STRUCTURED_ANALYSIS"], factory=FakeProvider)
    registry.register("citation", display_name="Citation", capabilities=["EVIDENCE_CITATION"], factory=FakeProvider)
    router = ProviderRouter(registry, priority=["citation", "heuristic"])
    route = router.resolve(ProviderCapability.STRUCTURED_ANALYSIS)
    assert route.provider_id == "heuristic"
    assert route.priority_rank == 2
    assert router.snapshot(ProviderCapability.STRUCTURED_ANALYSIS)["selected_provider_id"] == "heuristic"


def test_fallback_retries_then_uses_next_provider_without_fake_success():
    registry = ProviderRegistry(unavailable_after_failures=5, circuit_open_seconds=60)
    registry.register("first", display_name="First", capabilities=["STRUCTURED_ANALYSIS"], factory=lambda: FakeProvider(fail=True))
    registry.register("second", display_name="Second", capabilities=["STRUCTURED_ANALYSIS"], factory=FakeProvider)
    router = ProviderRouter(registry, priority=["first", "second"])
    fallback = FallbackProvider(
        registry,
        router,
        capability=ProviderCapability.STRUCTURED_ANALYSIS,
        retry_attempts=2,
        retry_backoff_seconds=0,
    )
    result = fallback.analyze({"synthetic": True})
    assert result["ok"] is True
    assert registry.health("first").failed_calls == 2
    assert registry.health("second").successful_calls == 1


def _analysis_result(text: str, provider: str) -> OpportunityAnalysisResult:
    return OpportunityAnalysisResult(
        summary=text,
        target_user="users",
        business_model="model",
        monetization="fee",
        risk_notes="risk",
        provider=provider,
    )


def test_conflict_selection_reports_fields_and_supports_majority_policy():
    candidates = [
        ProviderResultCandidate("first", 1, _analysis_result("same", "first")),
        ProviderResultCandidate("second", 2, _analysis_result("same", "second")),
        ProviderResultCandidate("third", 3, _analysis_result("different", "third")),
    ]
    selected, report = select_provider_result(candidates, selection_policy="majority")
    assert selected.provider_id == "first"
    assert report["status"] == "CONFLICT"
    assert report["conflicting_fields"] == ["summary"]
    assert report["selected_provider_id"] == "first"


def test_ensemble_runs_all_providers_and_persists_selection_report_in_result():
    class StaticProvider:
        def __init__(self, result):
            self.result = result

        def analyze(self, _payload):
            return self.result

    first = _analysis_result("first answer", "first")
    second = _analysis_result("second answer", "second")
    registry = ProviderRegistry()
    registry.register("first", display_name="First", capabilities=["STRUCTURED_ANALYSIS"], factory=lambda: StaticProvider(first))
    registry.register("second", display_name="Second", capabilities=["STRUCTURED_ANALYSIS"], factory=lambda: StaticProvider(second))
    ensemble = EnsembleProvider(
        registry,
        ProviderRouter(registry, priority=["first", "second"]),
        capability=ProviderCapability.STRUCTURED_ANALYSIS,
        retry_attempts=1,
        retry_backoff_seconds=0,
        selection_policy="priority",
    )
    result = ensemble.analyze({"synthetic": True})
    assert result.provider == "first"
    assert result.conflict_report["status"] == "CONFLICT"
    assert result.conflict_report["provider_ids"] == ["first", "second"]
