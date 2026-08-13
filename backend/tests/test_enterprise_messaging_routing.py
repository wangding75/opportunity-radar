from datetime import datetime
from types import SimpleNamespace

import pytest

from app.domain.enterprise_messaging import EnterpriseMessageResult, EnterpriseMessageStatus
from app.domain.enterprise_routing import (
    DEFAULT_ALERT_ENTERPRISE_TEMPLATE,
    EnterpriseMessageRoute,
    EnterpriseMessageTemplate,
    EnterpriseRoutingPolicy,
    EnterpriseRoutingStatus,
)
from app.services.enterprise_messaging_routing import build_alert_enterprise_message, route_alert_event, route_enterprise_message


def _request():
    return build_alert_enterprise_message(
        SimpleNamespace(
            id=42,
            event_key="synthetic-route-event",
            priority=2,
            title="SYNTHETIC opportunity",
            message="SYNTHETIC routing message",
            score=91,
            risk_score=12,
        ),
        EnterpriseMessageRoute(name="primary", provider="slack", destination="#synthetic"),
        data_class="SYNTHETIC",
        requested_at=datetime(2026, 8, 12, 12),
    )


class FakePort:
    def __init__(self, status: EnterpriseMessageStatus, *, error_code: str | None = None):
        self.status = status
        self.error_code = error_code
        self.calls = []

    def send(self, request):
        self.calls.append(request)
        return EnterpriseMessageResult(status=self.status, attempt=request.attempt, provider_message_id="synthetic-provider" if self.status == EnterpriseMessageStatus.SENT else None, error_code=self.error_code)


def test_alert_template_is_versioned_and_request_is_traceable():
    request = _request()
    assert request.message_id == "msg_alert_42_primary"
    assert request.idempotency_key.endswith("template:v1")
    assert request.metadata["alert_event_id"] == "42"
    assert request.metadata["data_class"] == "SYNTHETIC"
    assert "SYNTHETIC routing message" in request.text


def test_permanent_primary_failure_falls_back_and_marks_degraded():
    policy = EnterpriseRoutingPolicy(
        routes=[
            EnterpriseMessageRoute(name="primary", provider="slack", destination="#primary", priority=10),
            EnterpriseMessageRoute(name="backup", provider="feishu", destination="backup", priority=20),
        ]
    )
    primary = FakePort(EnterpriseMessageStatus.PERMANENT_FAILURE, error_code="SYNTHETIC_REJECTED")
    backup = FakePort(EnterpriseMessageStatus.SENT)
    result = route_enterprise_message(_request(), ports={"slack": primary, "feishu": backup}, policy=policy)
    assert result.status == EnterpriseRoutingStatus.DEGRADED
    assert result.fallback_used is True
    assert result.selected_route == "backup"
    assert len(result.attempts) == 2
    assert backup.calls[0].provider == "feishu"


def test_retryable_failure_is_deferred_by_default_and_can_be_configured_to_fallback():
    policy = EnterpriseRoutingPolicy(
        routes=[
            EnterpriseMessageRoute(name="primary", provider="slack", destination="#primary", priority=10),
            EnterpriseMessageRoute(name="backup", provider="wecom", destination="backup", priority=20),
        ]
    )
    primary = FakePort(EnterpriseMessageStatus.RETRYABLE_FAILURE, error_code="SYNTHETIC_TIMEOUT")
    backup = FakePort(EnterpriseMessageStatus.SENT)
    deferred = route_enterprise_message(_request(), ports={"slack": primary, "wecom": backup}, policy=policy)
    assert deferred.status == EnterpriseRoutingStatus.RETRYABLE
    assert len(deferred.attempts) == 1
    fallback = route_enterprise_message(
        _request(),
        ports={"slack": primary, "wecom": backup},
        policy=policy.model_copy(update={"fallback_on_retryable": True}),
    )
    assert fallback.status == EnterpriseRoutingStatus.DEGRADED


def test_empty_and_unconfigured_routes_never_report_success():
    empty = route_enterprise_message(_request(), ports={}, policy=EnterpriseRoutingPolicy())
    assert empty.status == EnterpriseRoutingStatus.NO_ROUTE
    missing = route_enterprise_message(
        _request(),
        ports={},
        policy=EnterpriseRoutingPolicy(routes=[EnterpriseMessageRoute(name="missing", provider="slack", destination="#missing")]),
    )
    assert missing.status == EnterpriseRoutingStatus.INVALID
    assert missing.final_result.error_code == "PROVIDER_NOT_CONFIGURED"


def test_route_policy_orders_deduplicates_and_rejects_duplicate_names():
    policy = EnterpriseRoutingPolicy(
        routes=[
            EnterpriseMessageRoute(name="backup", provider="feishu", destination="same", priority=20),
            EnterpriseMessageRoute(name="primary", provider="slack", destination="main", priority=10),
            EnterpriseMessageRoute(name="duplicate-target", provider="feishu", destination="same", priority=30),
        ]
    )
    assert [route.name for route in policy.ordered_routes()] == ["primary", "backup"]
    with pytest.raises(ValueError):
        EnterpriseRoutingPolicy(routes=[EnterpriseMessageRoute(name="same", provider="slack", destination="a"), EnterpriseMessageRoute(name="SAME", provider="feishu", destination="b")])


def test_template_rejects_unresolved_placeholders_and_no_route_alert_is_traceable():
    template = EnterpriseMessageTemplate(name="synthetic", version="v1", title="$missing", text="SYNTHETIC")
    with pytest.raises(ValueError):
        template.render({})
    event = SimpleNamespace(id=7, event_key="synthetic-no-route", priority=1, title="SYNTHETIC", message="", score=1, risk_score=2)
    result = route_alert_event(event, ports={}, policy=EnterpriseRoutingPolicy(), template=DEFAULT_ALERT_ENTERPRISE_TEMPLATE, data_class="SYNTHETIC")
    assert result.status == EnterpriseRoutingStatus.NO_ROUTE
    assert result.template_name == "alert.event"
