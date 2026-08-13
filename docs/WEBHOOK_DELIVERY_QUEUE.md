# Webhook Delivery Queue

`webhook_delivery_queue` is the durable delivery boundary between `AlertEvent` and a configured `WebhookEndpoint`.

## Contract and idempotency

- One row is created per `(alert_event_id, endpoint_id)` for enabled endpoints subscribed to `alert.event`.
- `event_id`, `delivery_id`, and `input_signature` are deterministic. Repeating enqueue returns `duplicates` and does not create another side effect.
- The row stores the canonical event JSON and the latest request/signature header for audit. It never serializes the endpoint secret.
- The event contract is `webhook-event-v1`; `X-Webhook-Signature` is `v1` HMAC-SHA256.

## State and retry

`QUEUED -> CLAIMED -> SENT`, with `RETRY_WAIT` for bounded exponential backoff. HTTP 408/425/429 and 5xx responses, network errors, and provider exceptions are retryable up to five attempts. Other HTTP 4xx responses are permanent failures. A disabled endpoint suppresses queued rows without sending them.

The worker re-signs the canonical event at each attempt with a fresh timestamp and a deterministic attempt nonce, so a delayed retry is not rejected only because its original queue timestamp is stale. A lease of five minutes makes an abandoned `CLAIMED` row reclaimable.

## Operations

- `POST /api/v1/alerts/webhooks/enqueue` — admin-only queue materialization; accepts optional `alert_event_ids`, `endpoint_ids`, `data_class`, and `limit`.
- `POST /api/v1/alerts/webhooks/process` — admin-only bounded processing.
- `GET /api/v1/alerts/webhooks/records` — delivery audit records with optional event, endpoint, and status filters.

The alerts worker runs enqueue/process only when `WEBHOOK_DELIVERY_ENABLED=true`; the default is fail-closed (`false`). HTTP transport uses the configured endpoint URL, no redirects, and `WEBHOOK_DELIVERY_TIMEOUT_SECONDS` (1–120 seconds). Tests use only SYNTHETIC data and injected provider ports.

`scripts/validate_webhook_delivery_docker.ps1` runs the full path against the Compose-only `mock-webhook` service. The receiver verifies HMAC-SHA256 with `MOCK_WEBHOOK_SECRET`, checks delivery-id consistency, deduplicates repeated delivery IDs, and labels every captured message `MOCK`; it is not an external production endpoint. `MOCK_WEBHOOK_FAILURE_MODE=retryable|permanent` is available for controlled retry/failure tests.
