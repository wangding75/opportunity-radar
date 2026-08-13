# Webhook endpoint configuration

T114-02 persists endpoint configuration in `webhook_endpoints` and exposes
RBAC-protected management routes:

- `GET /api/v1/webhooks/endpoints` lists safe configuration metadata.
- `POST /api/v1/webhooks/endpoints` creates an endpoint.
- `PATCH /api/v1/webhooks/endpoints/{id}` rotates the secret or updates the
  URL, event types, description, and enabled state.
- `DELETE /api/v1/webhooks/endpoints/{id}` removes an endpoint.

Mutation routes require admin scope and are covered by the existing audit
middleware. The secret is accepted only on create/rotate, stored separately
from the public configuration fields, and never returned by the API or
included in serialized audit details. Responses expose only a SHA-256 secret
fingerprint for rotation verification.

The URL validator forbids credentials, fragments, CR/LF injection, and local,
private, link-local, multicast, reserved, unspecified, and metadata targets.
Delivery performs a second DNS resolution check for every returned address and
uses `follow_redirects=false`. Controlled service names such as the Compose
`mock-webhook` must be listed in the exact-match `WEBHOOK_ALLOWED_HOSTS`
allowlist; the default is empty.
