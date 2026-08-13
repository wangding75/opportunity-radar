# Webhook event contract

T114-01 defines `webhook-event-v1` for later delivery and receiver tasks. The
signed HTTP body is the UTF-8, compact, recursively key-sorted JSON returned by
`canonical_event_bytes(WebhookEvent)`. Non-finite numbers, non-JSON values, and
payloads over 512 KiB are rejected.

An event contains a stable `event_id`, `event_type=alert.event`, event version,
UTC `occurred_at`, a `data_class`, and an evidence-linked payload. The signing
secret is never part of the event or delivery request model.

## HMAC header

`X-Webhook-Signature` is formatted as:

```text
t=<unix-seconds>,d=<delivery-id>,n=<nonce>,v1=<hex-hmac-sha256>
```

The HMAC input is `timestamp.delivery_id.nonce.canonical_body` with literal
period separators. Secrets must contain at least 16 bytes and may not contain
CR/LF. Receivers should use `verify_webhook_signature` with a bounded timestamp
tolerance; the default is five minutes and the boundary is inclusive.

`X-Webhook-Event`, `X-Webhook-Contract-Version`, and
`X-Webhook-Delivery-ID` are emitted by `build_webhook_headers`. Verification
uses constant-time comparison and rejects duplicate/missing signature fields,
tampered bodies, stale timestamps, wrong delivery IDs, and invalid secrets.
