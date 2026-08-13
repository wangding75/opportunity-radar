# Enterprise messaging templates and routing

T115-04 adds a provider-independent orchestration layer above the adapters.

- `DEFAULT_ALERT_ENTERPRISE_TEMPLATE` is versioned and renders traceable alert fields (`alert_event_id`, `event_key`, score, risk score, and data class) into plain text.
- `EnterpriseRoutingPolicy` orders enabled routes by priority, removes duplicate provider/destination targets, and never overwrites a route with a later duplicate.
- Permanent and invalid failures fall back by default. Retryable failures return `RETRYABLE` without a second side effect; set `fallback_on_retryable=true` only when the integration explicitly accepts that tradeoff.
- A successful backup is reported as `DEGRADED`, not `SENT`. All-failure, suppressed, invalid, and no-route states remain explicit.

Routes carry opaque destinations only; provider credentials remain in adapter configuration. Tests use `SYNTHETIC` messages and injected in-memory Ports.
