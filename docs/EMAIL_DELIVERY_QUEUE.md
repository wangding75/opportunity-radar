# Email delivery queue

T113-03 adds a durable, provider-neutral queue between `AlertEvent` and the
email adapter. It is intentionally separate from `alert_evaluation_queue`:
alert evaluation may be retried without repeating an external side effect.

## Contract

The queue stores one row per `AlertEvent` in `email_delivery_queue`. The row
contains the versioned `EmailDeliveryRequest` snapshot, normalized recipients,
template version, stable `input_signature`, provider message ID, attempt count,
failure classification, retry time, and a five-minute claim lease. No provider
credentials are persisted.

Normal state flow:

`QUEUED -> CLAIMED -> SENT`

Transient provider errors use `CLAIMED -> RETRY_WAIT -> CLAIMED` with bounded
exponential backoff (five attempts, 60 seconds to 60 minutes). Permanent,
suppressed, invalid, and retry-exhausted results are terminal. An expired
lease can be reclaimed by another worker.

The stable message and idempotency keys are derived from the alert event key
and template version. Repeating an enqueue request with the same recipients is
reported as a duplicate and does not create another row or provider side
effect. A changed recipient set is reported as a conflict and does not mutate
the existing request snapshot.

## API

The following routes are under `/api/v1` and require admin scope for writes:

- `POST /alerts/email/enqueue` with `{alert_event_ids?, recipients, data_class?, limit?}`
- `POST /alerts/email/process` with `{limit?}`
- `GET /alerts/email/records?alert_event_id=&status=&limit=`

All write requests pass through the existing request/trace ID and audit
middleware. The read endpoint is protected by the normal read boundary.

## Provider and worker safety

T113-03 uses the deterministic in-process `MockMailService`. T113-04 adds a
replaceable standard-library `SMTPMailService`; `EMAIL_DELIVERY_PROVIDER` may
be `mock` or `smtp`.
The worker is fail-closed by default:

```dotenv
EMAIL_DELIVERY_ENABLED=false
EMAIL_DELIVERY_PROVIDER=mock
EMAIL_DELIVERY_RECIPIENTS=
MOCK_MAIL_URL=http://mock-mail:8082
MOCK_MAIL_TIMEOUT_SECONDS=10
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_ADDRESS=
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_REQUIRE_AUTH=true
SMTP_TIMEOUT_SECONDS=10
```

Set `EMAIL_DELIVERY_ENABLED=true` only with an explicit comma-separated
`EMAIL_DELIVERY_RECIPIENTS` list. For SMTP, configure either STARTTLS or
implicit SSL, never both; production rejects plaintext SMTP and incomplete
authentication settings. `SMTP_PASSWORD` is read only from the process
environment and is never placed in the queue request or logs. Mock and
synthetic test data must be labeled `MOCK` or `SYNTHETIC`; no real external mail
is used by the automated tests. Docker acceptance can set
`EMAIL_DELIVERY_PROVIDER=mock_http` to route the queue through the Compose
`mock-mail` service; this provider is rejected for production-enabled delivery.
The repeatable acceptance command is
`powershell -File scripts/validate_email_delivery_docker.ps1`; it uses one
synthetic alert row and expects exactly one `SENT|1` queue result and one
`MOCK` message.
