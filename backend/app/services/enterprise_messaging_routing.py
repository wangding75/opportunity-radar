"""Template rendering, deterministic route ordering and explicit degradation."""

from __future__ import annotations

from datetime import datetime
from typing import Mapping

from app.core.time import as_utc_naive, utc_now
from app.db.models import AlertEvent
from app.domain.enterprise_messaging import (
    EnterpriseDataClass,
    EnterpriseMessageFailureKind,
    EnterpriseMessagePort,
    EnterpriseMessageRequest,
    EnterpriseMessageResult,
    EnterpriseMessageStatus,
)
from app.domain.enterprise_routing import (
    DEFAULT_ALERT_ENTERPRISE_TEMPLATE,
    EnterpriseMessageRoute,
    EnterpriseMessageTemplate,
    EnterpriseRoutingPolicy,
    EnterpriseRoutingResult,
    EnterpriseRoutingStatus,
)


def build_alert_enterprise_message(
    event: AlertEvent,
    route: EnterpriseMessageRoute,
    *,
    template: EnterpriseMessageTemplate = DEFAULT_ALERT_ENTERPRISE_TEMPLATE,
    data_class: EnterpriseDataClass = EnterpriseDataClass.ALERT_EVENT,
    requested_at: datetime | None = None,
) -> EnterpriseMessageRequest:
    data_class = EnterpriseDataClass(data_class)
    title, text = template.render(
        {
            "alert_event_id": event.id,
            "event_key": event.event_key,
            "priority": event.priority,
            "title": event.title,
            "message": event.message or "Alert event has no message.",
            "score": event.score,
            "risk_score": event.risk_score,
            "data_class": data_class.value,
        }
    )
    return EnterpriseMessageRequest(
        message_id=f"msg_alert_{event.id}_{route.name}",
        idempotency_key=f"alert_event:{event.id}:route:{route.name}:template:{template.version}",
        provider=route.provider,
        destination=route.destination,
        title=title,
        text=text,
        data_class=data_class,
        metadata={
            "contract_version": template.contract_version,
            "template_name": template.name,
            "template_version": template.version,
            "alert_event_id": str(event.id),
            "event_key": event.event_key,
            "data_class": data_class.value,
        },
        requested_at=as_utc_naive(requested_at or utc_now()),
    )


def _exception_result(request: EnterpriseMessageRequest, *, error: Exception) -> EnterpriseMessageResult:
    return EnterpriseMessageResult(
        status=EnterpriseMessageStatus.RETRYABLE_FAILURE,
        attempt=request.attempt,
        input_signature=None,
        observed_at=utc_now(),
        failure_kind=EnterpriseMessageFailureKind.TRANSIENT_PROVIDER,
        error_code="PROVIDER_EXCEPTION",
        error_detail=str(error)[:2_000],
    )


def _should_fallback(result: EnterpriseMessageResult, policy: EnterpriseRoutingPolicy) -> bool:
    if result.status == EnterpriseMessageStatus.RETRYABLE_FAILURE:
        return policy.fallback_on_retryable
    if result.status == EnterpriseMessageStatus.PERMANENT_FAILURE:
        return policy.fallback_on_permanent
    if result.status == EnterpriseMessageStatus.INVALID:
        return policy.fallback_on_invalid
    return False


def route_enterprise_message(
    request: EnterpriseMessageRequest,
    *,
    ports: Mapping[str, EnterpriseMessagePort],
    policy: EnterpriseRoutingPolicy,
) -> EnterpriseRoutingResult:
    """Try routes in priority order without converting failure into success."""

    routes = policy.ordered_routes()
    if not routes:
        return EnterpriseRoutingResult(status=EnterpriseRoutingStatus.NO_ROUTE, attempts=[])
    attempts: list[dict] = []
    final_result: EnterpriseMessageResult | None = None
    selected_route: str | None = None
    fallback_used = False
    for index, route in enumerate(routes):
        port = ports.get(route.provider)
        routed_request = request.model_copy(update={"provider": route.provider, "destination": route.destination})
        if port is None:
            result = EnterpriseMessageResult(
                status=EnterpriseMessageStatus.INVALID,
                attempt=routed_request.attempt,
                input_signature=None,
                observed_at=utc_now(),
                failure_kind=EnterpriseMessageFailureKind.INVALID_DESTINATION,
                error_code="PROVIDER_NOT_CONFIGURED",
                error_detail=f"no enterprise messaging port is configured for {route.provider}",
            )
        else:
            try:
                result = port.send(routed_request)
            except Exception as exc:
                result = _exception_result(routed_request, error=exc)
        final_result = result
        attempts.append(
            {
                "route": route.name,
                "provider": route.provider,
                "destination": route.destination,
                "status": result.status.value,
                "attempt": result.attempt,
                "error_code": result.error_code,
            }
        )
        if result.status in {EnterpriseMessageStatus.SENT, EnterpriseMessageStatus.ACCEPTED}:
            selected_route = route.name
            status = EnterpriseRoutingStatus.DEGRADED if fallback_used else EnterpriseRoutingStatus.SENT
            return EnterpriseRoutingResult(
                status=status,
                selected_route=selected_route,
                provider_message_id=result.provider_message_id,
                fallback_used=fallback_used,
                attempts=attempts,
                final_result=result,
            )
        if result.status == EnterpriseMessageStatus.SUPPRESSED:
            return EnterpriseRoutingResult(status=EnterpriseRoutingStatus.SUPPRESSED, attempts=attempts, final_result=result)
        if index == len(routes) - 1 or not _should_fallback(result, policy):
            status = {
                EnterpriseMessageStatus.RETRYABLE_FAILURE: EnterpriseRoutingStatus.RETRYABLE,
                EnterpriseMessageStatus.INVALID: EnterpriseRoutingStatus.INVALID,
            }.get(result.status, EnterpriseRoutingStatus.FAILED)
            return EnterpriseRoutingResult(status=status, attempts=attempts, final_result=result)
        fallback_used = True
    return EnterpriseRoutingResult(status=EnterpriseRoutingStatus.FAILED, attempts=attempts, final_result=final_result)


def route_alert_event(
    event: AlertEvent,
    *,
    ports: Mapping[str, EnterpriseMessagePort],
    policy: EnterpriseRoutingPolicy,
    template: EnterpriseMessageTemplate = DEFAULT_ALERT_ENTERPRISE_TEMPLATE,
    data_class: EnterpriseDataClass = EnterpriseDataClass.ALERT_EVENT,
    requested_at: datetime | None = None,
) -> EnterpriseRoutingResult:
    routes = policy.ordered_routes()
    if not routes:
        return EnterpriseRoutingResult(status=EnterpriseRoutingStatus.NO_ROUTE, template_name=template.name, template_version=template.version)
    request = build_alert_enterprise_message(event, routes[0], template=template, data_class=data_class, requested_at=requested_at)
    result = route_enterprise_message(request, ports=ports, policy=policy)
    return result.model_copy(update={"template_name": template.name, "template_version": template.version})
