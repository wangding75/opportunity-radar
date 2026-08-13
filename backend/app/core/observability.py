from __future__ import annotations

import json
import logging
import threading
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import AlertEvaluationQueue, EmailDeliveryRecord, Opportunity, ProbeTask, SourceHealthState, WebhookDeliveryRecord, WorkerHeartbeat
from app.services.sanitizer import redact_log_text
from datetime import datetime, timedelta, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_log_text(record.getMessage()),
        }
        for key in ("request_id", "trace_id", "path", "method", "status_code", "duration_ms", "worker_id", "mode"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = redact_log_text(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging() -> None:
    root = logging.getLogger()
    if getattr(root, "_opportunity_radar_json_configured", False):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.handlers[:] = [handler]
    root.setLevel(logging.INFO)
    root._opportunity_radar_json_configured = True  # type: ignore[attr-defined]


class Metrics:
    _buckets = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.requests: Counter[tuple[str, str, int]] = Counter()
        self.duration_count: Counter[tuple[str, str]] = Counter()
        self.duration_sum: Counter[tuple[str, str]] = Counter()
        self.duration_buckets: Counter[tuple[str, str, float]] = Counter()
        self.provider_calls: Counter[tuple[str, str]] = Counter()
        self.provider_retries: Counter[str] = Counter()
        self.provider_fallbacks: Counter[tuple[str, str]] = Counter()
        self.provider_selections: Counter[tuple[str, str]] = Counter()
        self.provider_conflicts: Counter[str] = Counter()

    @staticmethod
    def _safe_label(value: str) -> str:
        return value.replace("\\", "\\\\").replace("\n", " ").replace('"', '\\"')[:300]

    def observe_http(self, method: str, path: str, status: int, seconds: float) -> None:
        key = (method, path)
        with self._lock:
            self.requests[(method, path, status)] += 1
            self.duration_count[key] += 1
            self.duration_sum[key] += seconds
            for bucket in self._buckets:
                if seconds <= bucket:
                    self.duration_buckets[(method, path, bucket)] += 1

    def observe_provider_call(self, provider_id: str, outcome: str) -> None:
        with self._lock:
            self.provider_calls[(str(provider_id), str(outcome))] += 1

    def observe_provider_retry(self, provider_id: str) -> None:
        with self._lock:
            self.provider_retries[str(provider_id)] += 1

    def observe_provider_fallback(self, from_provider: str, to_provider: str) -> None:
        with self._lock:
            self.provider_fallbacks[(str(from_provider), str(to_provider))] += 1

    def observe_provider_selection(self, selection_policy: str, provider_id: str) -> None:
        with self._lock:
            self.provider_selections[(str(selection_policy), str(provider_id))] += 1

    def observe_provider_conflict(self, status: str) -> None:
        with self._lock:
            self.provider_conflicts[str(status)] += 1

    def render_prometheus(self) -> str:
        lines = [
            "# HELP opportunity_radar_http_requests_total HTTP requests processed.",
            "# TYPE opportunity_radar_http_requests_total counter",
        ]
        with self._lock:
            for (method, path, status), value in sorted(self.requests.items()):
                lines.append(f'opportunity_radar_http_requests_total{{method="{self._safe_label(method)}",path="{self._safe_label(path)}",status="{status}"}} {value}')
            lines += [
                "# HELP opportunity_radar_http_request_duration_seconds HTTP request duration.",
                "# TYPE opportunity_radar_http_request_duration_seconds histogram",
            ]
            keys = sorted(self.duration_count)
            for method, path in keys:
                for bucket in self._buckets:
                    value = self.duration_buckets[(method, path, bucket)]
                    lines.append(f'opportunity_radar_http_request_duration_seconds_bucket{{method="{self._safe_label(method)}",path="{self._safe_label(path)}",le="{bucket}"}} {value}')
                count = self.duration_count[(method, path)]
                total = self.duration_sum[(method, path)]
                labels = f'method="{self._safe_label(method)}",path="{self._safe_label(path)}"'
                lines.append(f'opportunity_radar_http_request_duration_seconds_bucket{{{labels},le="+Inf"}} {count}')
                lines.append(f'opportunity_radar_http_request_duration_seconds_sum{{{labels}}} {total:.9f}')
                lines.append(f'opportunity_radar_http_request_duration_seconds_count{{{labels}}} {count}')
            lines += [
                "# HELP opportunity_radar_analysis_provider_calls_total Analysis provider calls by outcome.",
                "# TYPE opportunity_radar_analysis_provider_calls_total counter",
            ]
            for (provider_id, outcome), value in sorted(self.provider_calls.items()):
                lines.append(f'opportunity_radar_analysis_provider_calls_total{{provider="{self._safe_label(provider_id)}",outcome="{self._safe_label(outcome)}"}} {value}')
            lines += [
                "# HELP opportunity_radar_analysis_provider_retries_total Analysis provider retry attempts.",
                "# TYPE opportunity_radar_analysis_provider_retries_total counter",
            ]
            for provider_id, value in sorted(self.provider_retries.items()):
                lines.append(f'opportunity_radar_analysis_provider_retries_total{{provider="{self._safe_label(provider_id)}"}} {value}')
            lines += [
                "# HELP opportunity_radar_analysis_provider_fallbacks_total Analysis provider fallback transitions.",
                "# TYPE opportunity_radar_analysis_provider_fallbacks_total counter",
            ]
            for (from_provider, to_provider), value in sorted(self.provider_fallbacks.items()):
                lines.append(f'opportunity_radar_analysis_provider_fallbacks_total{{from_provider="{self._safe_label(from_provider)}",to_provider="{self._safe_label(to_provider)}"}} {value}')
            lines += [
                "# HELP opportunity_radar_analysis_provider_selections_total Selected analysis provider by policy.",
                "# TYPE opportunity_radar_analysis_provider_selections_total counter",
            ]
            for (selection_policy, provider_id), value in sorted(self.provider_selections.items()):
                lines.append(f'opportunity_radar_analysis_provider_selections_total{{policy="{self._safe_label(selection_policy)}",provider="{self._safe_label(provider_id)}"}} {value}')
            lines += [
                "# HELP opportunity_radar_analysis_provider_conflicts_total Provider result conflict status.",
                "# TYPE opportunity_radar_analysis_provider_conflicts_total counter",
            ]
            for status, value in sorted(self.provider_conflicts.items()):
                lines.append(f'opportunity_radar_analysis_provider_conflicts_total{{status="{self._safe_label(status)}"}} {value}')
        return "\n".join(lines) + "\n"


def render_database_metrics(db: Session, *, worker_stale_seconds: int) -> str:
    now = utc_now()
    stale_cutoff = now - timedelta(seconds=worker_stale_seconds)
    gauges = {
        "opportunity_radar_probe_tasks_active": db.scalar(select(func.count()).select_from(ProbeTask).where(ProbeTask.active.is_(True))) or 0,
        "opportunity_radar_alert_evaluation_queue_pending": db.scalar(select(func.count()).select_from(AlertEvaluationQueue)) or 0,
        "opportunity_radar_email_delivery_queue_pending": db.scalar(
            select(func.count()).select_from(EmailDeliveryRecord).where(EmailDeliveryRecord.status.in_(["QUEUED", "CLAIMED", "RETRY_WAIT"]))
        ) or 0,
        "opportunity_radar_webhook_delivery_queue_pending": db.scalar(
            select(func.count()).select_from(WebhookDeliveryRecord).where(WebhookDeliveryRecord.status.in_(["QUEUED", "CLAIMED", "RETRY_WAIT"]))
        ) or 0,
        "opportunity_radar_analysis_pending": db.scalar(select(func.count()).select_from(Opportunity).where(Opportunity.analysis_status.in_(["PENDING", "ANALYZING", "DEGRADED"]))) or 0,
        "opportunity_radar_source_circuits_open": db.scalar(select(func.count()).select_from(SourceHealthState).where(SourceHealthState.status == "CIRCUIT_OPEN")) or 0,
        "opportunity_radar_workers_stale": db.scalar(select(func.count()).select_from(WorkerHeartbeat).where(WorkerHeartbeat.last_seen_at < stale_cutoff)) or 0,
    }
    lines: list[str] = []
    for name, value in gauges.items():
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {int(value)}")
    return "\n".join(lines) + "\n"


metrics = Metrics()
