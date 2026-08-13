# Mock Mail Service

T113-02 provides `MockMailService` as the deterministic implementation of
`EmailDeliveryPort` and exposes it through `python -m app.mock_mail_service`.
The HTTP API is:

- `GET /health` — returns provider/version and `data_class=MOCK`.
- `POST /v1/send` — validates an `EmailDeliveryRequest` and returns a
  versioned `EmailDeliveryResult`.
- `GET /v1/messages?limit=...` — returns the bounded in-memory accepted
  mailbox.
- `POST /v1/reset` — clears the test mailbox and idempotency state.

Repeated requests with the same contract input signature return the same
provider message ID and do not create another mailbox message. Tests can set
`X-Mock-Failure` to `transient`, `rate_limited`, `permanent`, or `suppressed`;
the result status remains explicit and is never reported as `SENT`. The service
stores no real external data and all responses are marked `MOCK`.
