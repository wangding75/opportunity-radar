# Keys, logs, configuration and container security review

`validation/security_review_keys_logs_config.json` records eight PASS controls
for secret handling, database CLI credentials, log/audit redaction, repository
and Compose boundaries, non-root containers, Mock separation, and locked
dependencies/SBOM. The validator requires real code and tests for every control
and zero live data.

The review also hardens the implementation: audit query strings now remove
sensitive fields, structured messages and tracebacks redact common secret forms
and URL userinfo, and the production image runs as `appuser` UID/GID 10001.
The archive path is prepared and owned by that user before Compose mounts the
write volume.

Run the validator:

```text
python scripts/validate_security_review_keys_logs_config.py
```
