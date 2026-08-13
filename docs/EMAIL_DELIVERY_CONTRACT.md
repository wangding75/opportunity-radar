# Email delivery contract

`email-delivery-v1` is the provider-neutral boundary used by later Mock Mail
and SMTP adapters. Requests contain a stable message ID and idempotency key,
normalized unique recipients, a versioned template name/version, subject,
plain-text body, optional HTML body, request time, and non-secret metadata.
Subjects reject CR/LF injection; recipient and body limits are policy bounded.

Templates are versioned and require a plain-text body. Rendering fails closed
when a placeholder is missing or produces a subject with CR/LF. The request
signature excludes request time, so retries and replay share the same identity.

Results use explicit `SENT`, `RETRYABLE_FAILURE`, `PERMANENT_FAILURE`,
`SUPPRESSED`, and `INVALID` statuses. Transient-provider and rate-limit errors
are retryable only before the configured attempt limit, with bounded exponential
backoff. Permanent failures never receive a retry time. A `SENT` result must
include a provider message ID. The `EmailDeliveryPort` protocol keeps core
alert logic independent of Mock/SMTP implementations.
