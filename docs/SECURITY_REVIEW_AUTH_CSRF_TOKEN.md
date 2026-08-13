# Authentication, session, CSRF and token security review

`validation/security_review_auth.json` records eight PASS controls for the
authentication boundary. `scripts/validate_security_review_auth.py` checks that
each control has real code and regression-test targets, uses only
SYNTHETIC/MOCK evidence, and remains PASS.

The review covers production fail-closed settings, secure session cookies,
CSRF enforcement, personal-token hashing/expiry/revocation, scrypt password
verification and lockout behavior, RBAC scope limits, frontend cookie handling,
and request/audit correlation. The additional regression tests cover production
`Secure; SameSite=Strict` cookies and invalid/missing CSRF tokens.

Run the review validator:

```text
python scripts/validate_security_review_auth.py
```

No live account, provider, or external data is used.
