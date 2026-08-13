# Security regression gate

`scripts/validate_security_gate.py` is the aggregate T118 security gate. It
reruns and requires PASS for:

- authentication, session, CSRF and personal-token controls (8);
- input/output, SSRF, XML and HTTP boundaries (8);
- keys, logs, configuration and container controls (8);
- dependency and supply-chain controls (6); and
- the T117 false-completion regression gate (6 checks, zero violations and
  zero functional gaps).

The gate writes `validation/security_gate.json`, uses only SYNTHETIC/MOCK
validation data, and is invoked by `scripts/validate_product.sh`:

```text
python scripts/validate_security_gate.py
```
