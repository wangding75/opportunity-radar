# Production HTTPS deployment

The production Compose file exposes only the Caddy reverse proxy on ports 80 and
443. The API listens on port 8000 inside the Compose network and is not
published on the host. Browser traffic must therefore use the proxy URL.

## Domain and certificates

Set `PUBLIC_DOMAIN` to a DNS name whose A/AAAA records point to the deployment
host. Caddy obtains and renews a public ACME certificate automatically. Ports
80 and 443 must be reachable from the Internet for the normal HTTP-01
challenge and browser access; PostgreSQL and API port 8000 must not be opened
publicly.

Do not commit a private key, password, or real production domain. Caddy stores
issued certificates in the named `caddy_data` volume. Back up that volume using
the deployment platform's protected secret/volume process.

The proxy explicitly forwards `Host`, `X-Forwarded-Proto`, and
`X-Forwarded-For`. Caddy's trusted proxy policy only accepts private network
ranges as upstream proxies and uses strict parsing; arbitrary Internet
clients are not treated as trusted proxy sources.

## Local HTTPS smoke

For a complete local redirect smoke, use the standard 80/443 mappings with
`PUBLIC_DOMAIN=localhost`:

```powershell
$env:PUBLIC_DOMAIN = "localhost"
docker compose up -d --build
```

Caddy serves HTTPS with its local internal certificate. A browser must trust
Caddy's local CA, or a test client may deliberately use a local-only insecure
TLS context. This is only a development smoke mode; production remains HTTPS
with Secure session and CSRF cookies.

The HTTP listener is retained for ACME and redirects normal site requests to
HTTPS. Public production ingress is therefore `80/tcp` and `443/tcp`; API
`8000/tcp` and PostgreSQL `5432/tcp` remain internal.

If 80/443 are occupied locally, set `HTTP_PORT` and `HTTPS_PORT` to free host
ports and test HTTPS directly on the chosen HTTPS port. The HTTP redirect is
constructed for the canonical HTTPS port, so a full redirect check should use
the standard 80/443 mapping.
