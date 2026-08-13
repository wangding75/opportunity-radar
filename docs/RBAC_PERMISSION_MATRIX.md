# RBAC permission matrix

The frozen authorization contract lives in
`backend/app/services/permissions.py` and is mirrored by
`validation/rbac_permission_matrix.json`. The validator rejects drift between
the runtime contract and the committed review artifact.

| Role | Read product data | Write research/rules | Admin operations | Owner account boundary |
| --- | --- | --- | --- | --- |
| VIEWER | Yes | No | No | No |
| RESEARCHER | Yes | Yes | No | No |
| ADMIN | Yes | Yes | Yes | No |
| OWNER | Yes | Yes | Yes | Yes |

Rules that apply across the matrix:

- A live role caps personal-token scopes; a token can narrow but never elevate
  the current role.
- Session mutations require the CSRF contract. Personal-token mutations require
  the token scope and the live role.
- Only OWNER may create or mutate an OWNER account, and the last enabled OWNER
  cannot be removed or disabled.
- Production authentication is fail-closed with `AUTH_MODE=rbac`.

Run the contract check with:

```text
python scripts/validate_rbac_permission_matrix.py
```
