# Login rate limiting and audit actor trust

Production login has two independent protections:

- the existing per-account failure counter and 15-minute account lockout;
- shared SQL `login_rate_limits` counters keyed by a one-way digest of source
  IP and normalized username, with configurable window, threshold and block
  duration. The counters are stored in PostgreSQL, so API workers share the
  same decision, and stale rows are deleted during login/retention cleanup.

Configure `LOGIN_RATE_LIMIT_WINDOW_SECONDS`, `LOGIN_RATE_LIMIT_MAX_ATTEMPTS`
and `LOGIN_RATE_LIMIT_BLOCK_SECONDS` for the deployment. Login failures return
the same generic message for unknown, disabled, wrong-password and throttled
subjects; throttled responses use `429` and `Retry-After` without revealing
whether a username exists.

When the API is behind a reverse proxy, configure that proxy's source network
in `TRUSTED_PROXY_CIDRS` if the application must use the original client IP for
the source bucket. Otherwise forwarded source headers are ignored and the
proxy peer address is used, which intentionally favors a conservative shared
limit over trusting spoofable headers.

Audit actor identity is server-derived. An authenticated session or API token
always supplies the actor from its verified principal. Anonymous requests use
`anonymous`; login requests use a stable one-way `login:<digest>` subject. A
client cannot set `X-Actor` to change either value.

Proxy actor injection is disabled by default. If an organization explicitly
needs it, set `AUDIT_TRUSTED_PROXY_ACTOR=true` and list only controlled proxy
networks in `TRUSTED_PROXY_CIDRS`. The application accepts the actor header
only when the direct peer address belongs to one of those CIDRs and records it
as `proxy:<value>`. This setting must be reviewed together with the reverse
proxy configuration; forwarded headers from an untrusted peer are ignored.
