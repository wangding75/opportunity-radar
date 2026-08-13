# API permission inventory

The API inventory is generated from the live FastAPI `APIRoute` dependency
graph. It does not rely on a manually maintained route list: adding or changing
`require_read_auth`, `require_write_auth`, or `require_admin_auth` changes the
derived contract and causes validation to fail until the committed artifact is
regenerated.

Generate and validate it with:

```text
python scripts/generate_api_permission_inventory.py
python scripts/validate_api_permission_inventory.py
```

The generated artifact is
`validation/api_permission_inventory.json`. Each route records its methods,
path, dependency names, required scope, minimum role, allowed roles, CSRF
requirement for session mutations, and the interactive-session rule for
personal-token issuance. The same contract is emitted as `x-rbac` in the
generated OpenAPI operations.

The inventory is metadata only and collects no external data; its data policy
is `SYNTHETIC_OR_MOCK_ONLY` with `real_data_collected=0`.
