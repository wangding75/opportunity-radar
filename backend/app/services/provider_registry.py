from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
import time
from typing import Any, Callable, Iterable

from app.core.time import utc_now
from app.core.observability import metrics
from app.services.provider_conflict import ProviderResultCandidate, select_provider_result


class ProviderCapability(StrEnum):
    STRUCTURED_ANALYSIS = "STRUCTURED_ANALYSIS"
    EVIDENCE_CITATION = "EVIDENCE_CITATION"


class ProviderHealthStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class ProviderRegistryError(RuntimeError):
    pass


class ProviderNotFoundError(ProviderRegistryError):
    pass


class ProviderUnavailableError(ProviderRegistryError):
    pass


class ProviderExecutionError(ProviderRegistryError):
    pass


@dataclass(frozen=True)
class ProviderRoute:
    provider_id: str
    capability: ProviderCapability
    priority_rank: int
    reason: str


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    display_name: str
    capabilities: frozenset[ProviderCapability]
    factory: Callable[[], Any]
    enabled: bool = True

    def supports(self, capability: ProviderCapability) -> bool:
        return capability in self.capabilities


@dataclass
class ProviderHealth:
    status: ProviderHealthStatus = ProviderHealthStatus.UNKNOWN
    consecutive_failures: int = 0
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error: str | None = None
    circuit_open_until: datetime | None = None

    def mark_success(self, *, now: datetime | None = None) -> None:
        now = now or utc_now()
        self.status = ProviderHealthStatus.HEALTHY
        self.consecutive_failures = 0
        self.total_calls += 1
        self.successful_calls += 1
        self.last_success_at = now
        self.last_error = None
        self.circuit_open_until = None

    def mark_failure(
        self,
        error: str,
        *,
        now: datetime | None = None,
        unavailable_after: int = 3,
        circuit_open_seconds: float = 60.0,
    ) -> None:
        now = now or utc_now()
        self.total_calls += 1
        self.failed_calls += 1
        self.consecutive_failures += 1
        self.last_failure_at = now
        self.last_error = str(error)[:2_000]
        self.status = (
            ProviderHealthStatus.UNAVAILABLE
            if self.consecutive_failures >= max(1, unavailable_after)
            else ProviderHealthStatus.DEGRADED
        )
        if self.status == ProviderHealthStatus.UNAVAILABLE:
            from datetime import timedelta
            self.circuit_open_until = now + timedelta(seconds=max(1.0, circuit_open_seconds))

    def can_attempt(self, *, now: datetime | None = None) -> bool:
        now = now or utc_now()
        if self.status != ProviderHealthStatus.UNAVAILABLE:
            return True
        if self.circuit_open_until is not None and now >= self.circuit_open_until:
            self.status = ProviderHealthStatus.DEGRADED
            return True
        return False


@dataclass
class ProviderRegistry:
    unavailable_after_failures: int = 3
    circuit_open_seconds: float = 60.0
    _descriptors: dict[str, ProviderDescriptor] = field(default_factory=dict)
    _health: dict[str, ProviderHealth] = field(default_factory=dict)

    def register(
        self,
        provider_id: str,
        *,
        display_name: str,
        capabilities: Iterable[ProviderCapability | str],
        factory: Callable[[], Any],
        enabled: bool = True,
    ) -> ProviderDescriptor:
        provider_id = str(provider_id or "").strip().lower()
        if not provider_id:
            raise ValueError("provider_id must not be empty")
        if provider_id in self._descriptors:
            raise ValueError(f"provider already registered: {provider_id}")
        normalized_capabilities = frozenset(
            capability if isinstance(capability, ProviderCapability) else ProviderCapability(str(capability).strip().upper())
            for capability in capabilities
        )
        descriptor = ProviderDescriptor(
            provider_id=provider_id,
            display_name=str(display_name or provider_id).strip(),
            capabilities=normalized_capabilities,
            factory=factory,
            enabled=bool(enabled),
        )
        self._descriptors[provider_id] = descriptor
        self._health.setdefault(provider_id, ProviderHealth())
        return descriptor

    def descriptor(self, provider_id: str) -> ProviderDescriptor:
        try:
            return self._descriptors[str(provider_id).strip().lower()]
        except KeyError as exc:
            raise ProviderNotFoundError(f"unknown analysis provider: {provider_id}") from exc

    def create(self, provider_id: str) -> Any:
        descriptor = self.descriptor(provider_id)
        if not descriptor.enabled:
            raise ProviderUnavailableError(f"analysis provider is disabled: {descriptor.provider_id}")
        try:
            provider = descriptor.factory()
        except Exception as exc:
            self.mark_failure(descriptor.provider_id, exc)
            raise
        setattr(provider, "provider_id", descriptor.provider_id)
        return provider

    def create_tracked(self, provider_id: str) -> "HealthTrackedProvider":
        return HealthTrackedProvider(self, str(provider_id).strip().lower(), self.create(provider_id))

    def mark_success(self, provider_id: str, *, now: datetime | None = None) -> None:
        self.descriptor(provider_id)
        self._health[str(provider_id).strip().lower()].mark_success(now=now)

    def mark_failure(self, provider_id: str, error: Any, *, now: datetime | None = None) -> None:
        self.descriptor(provider_id)
        self._health[str(provider_id).strip().lower()].mark_failure(
            str(error),
            now=now,
            unavailable_after=self.unavailable_after_failures,
            circuit_open_seconds=self.circuit_open_seconds,
        )

    def health(self, provider_id: str) -> ProviderHealth:
        self.descriptor(provider_id)
        return self._health[str(provider_id).strip().lower()]

    def snapshot(self) -> list[dict[str, Any]]:
        rows = []
        for provider_id in sorted(self._descriptors):
            descriptor = self._descriptors[provider_id]
            health = self._health[provider_id]
            rows.append({
                "provider_id": provider_id,
                "display_name": descriptor.display_name,
                "capabilities": sorted(capability.value for capability in descriptor.capabilities),
                "enabled": descriptor.enabled,
                "health": {
                    "status": health.status.value,
                    "consecutive_failures": health.consecutive_failures,
                    "total_calls": health.total_calls,
                    "successful_calls": health.successful_calls,
                    "failed_calls": health.failed_calls,
                    "last_success_at": health.last_success_at,
                    "last_failure_at": health.last_failure_at,
                    "last_error": health.last_error,
                    "circuit_open_until": health.circuit_open_until,
                },
            })
        return rows


class ProviderRouter:
    def __init__(
        self,
        registry: ProviderRegistry,
        *,
        priority: Iterable[str] = (),
        default_provider_id: str | None = None,
    ) -> None:
        self.registry = registry
        configured = [str(provider_id).strip().lower() for provider_id in priority if str(provider_id).strip()]
        if len(configured) != len(set(configured)):
            raise ValueError("ANALYSIS_PROVIDER_PRIORITY must not contain duplicates")
        self.priority = configured or ([str(default_provider_id).strip().lower()] if default_provider_id else [])

    def resolve(self, capability: ProviderCapability) -> ProviderRoute:
        routes = self.candidates(capability)
        if routes:
            return routes[0]
        raise ProviderUnavailableError(
            f"no enabled provider supports capability: {capability.value}; priority={','.join(self.priority)}"
        )

    def candidates(self, capability: ProviderCapability) -> list[ProviderRoute]:
        if not self.priority:
            raise ProviderUnavailableError(f"no provider priority configured for capability: {capability.value}")
        routes: list[ProviderRoute] = []
        for rank, provider_id in enumerate(self.priority, start=1):
            descriptor = self.registry.descriptor(provider_id)
            if descriptor.enabled and descriptor.supports(capability):
                routes.append(ProviderRoute(
                    provider_id=descriptor.provider_id,
                    capability=capability,
                    priority_rank=rank,
                    reason="first enabled provider matching requested capability",
                ))
        return routes

    def snapshot(self, capability: ProviderCapability) -> dict[str, Any]:
        try:
            route = self.resolve(capability)
        except ProviderRegistryError as exc:
            return {
                "capability": capability.value,
                "priority": list(self.priority),
                "selected_provider_id": None,
                "error": str(exc),
            }
        return {
            "capability": route.capability.value,
            "priority": list(self.priority),
            "selected_provider_id": route.provider_id,
            "priority_rank": route.priority_rank,
            "reason": route.reason,
        }


class HealthTrackedProvider:
    def __init__(self, registry: ProviderRegistry, provider_id: str, provider: Any) -> None:
        self.registry = registry
        self.provider_id = provider_id
        self.provider = provider

    def analyze(self, payload):
        try:
            result = self.provider.analyze(payload)
        except Exception as exc:
            self.registry.mark_failure(self.provider_id, exc)
            metrics.observe_provider_call(self.provider_id, "failure")
            raise
        self.registry.mark_success(self.provider_id)
        metrics.observe_provider_call(self.provider_id, "success")
        return result

    def close(self) -> None:
        close = getattr(self.provider, "close", None)
        if close is not None:
            close()


class FallbackProvider:
    """Execute a bounded retry/fallback policy over registered providers."""

    def __init__(
        self,
        registry: ProviderRegistry,
        router: ProviderRouter,
        *,
        capability: ProviderCapability,
        retry_attempts: int = 2,
        retry_backoff_seconds: float = 0.25,
    ) -> None:
        self.registry = registry
        self.router = router
        self.capability = capability
        self.retry_attempts = max(1, min(5, int(retry_attempts)))
        self.retry_backoff_seconds = max(0.0, min(60.0, float(retry_backoff_seconds)))
        self.provider_id = "ensemble"
        self._providers: dict[str, HealthTrackedProvider] = {}

    def _provider(self, provider_id: str) -> HealthTrackedProvider:
        provider = self._providers.get(provider_id)
        if provider is None:
            provider = self.registry.create_tracked(provider_id)
            self._providers[provider_id] = provider
        return provider

    def _run_route(self, route: ProviderRoute, payload, errors: list[str]):
        health = self.registry.health(route.provider_id)
        if not health.can_attempt():
            errors.append(f"{route.provider_id}: circuit open")
            return None
        try:
            provider = self._provider(route.provider_id)
        except Exception as exc:
            errors.append(f"{route.provider_id}: provider creation failed: {exc}")
            metrics.observe_provider_call(route.provider_id, "failure")
            return None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                return provider.analyze(payload)
            except Exception as exc:
                errors.append(f"{route.provider_id} attempt {attempt}: {exc}")
                if attempt < self.retry_attempts and self.retry_backoff_seconds:
                    metrics.observe_provider_retry(route.provider_id)
                    time.sleep(self.retry_backoff_seconds)
                elif attempt < self.retry_attempts:
                    metrics.observe_provider_retry(route.provider_id)
        return None

    def analyze(self, payload):
        errors: list[str] = []
        previous_provider_id: str | None = None
        for route in self.router.candidates(self.capability):
            if previous_provider_id is not None:
                metrics.observe_provider_fallback(previous_provider_id, route.provider_id)
            result = self._run_route(route, payload, errors)
            if result is not None:
                metrics.observe_provider_selection("fallback", route.provider_id)
                return result
            previous_provider_id = route.provider_id
        detail = "; ".join(errors)[:4_000] or "no provider attempted"
        raise ProviderExecutionError(f"all analysis providers failed: {detail}")

    def close(self) -> None:
        for provider in self._providers.values():
            provider.close()


class EnsembleProvider(FallbackProvider):
    """Run every eligible provider and select one result with an audit report."""

    def __init__(self, *args, selection_policy: str = "priority", **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.selection_policy = selection_policy

    def analyze(self, payload):
        candidates: list[ProviderResultCandidate] = []
        errors: list[str] = []
        for route in self.router.candidates(self.capability):
            result = self._run_route(route, payload, errors)
            if result is not None:
                candidates.append(ProviderResultCandidate(
                    provider_id=route.provider_id,
                    priority_rank=route.priority_rank,
                    result=result,
                ))
        if not candidates:
            detail = "; ".join(errors)[:4_000] or "no provider attempted"
            raise ProviderExecutionError(f"all analysis providers failed: {detail}")
        selected, report = select_provider_result(
            candidates,
            selection_policy=self.selection_policy,
            errors=errors,
        )
        metrics.observe_provider_selection(self.selection_policy, selected.provider_id)
        metrics.observe_provider_conflict(report["status"])
        return replace(selected.result, provider=selected.provider_id, conflict_report=report)
