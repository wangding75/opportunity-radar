# RBAC boundary review

`backend/tests/test_rbac_boundaries.py` is the regression suite for the
vertical and horizontal authorization boundaries. It uses only an isolated
SQLite database and synthetic users/tokens.

The suite verifies:

- anonymous requests are rejected from protected product reads;
- VIEWER can read but cannot write or run admin operations;
- RESEARCHER can update research/watch state but cannot ingest evidence, run
  operations, or mutate users;
- ADMIN can run admin operations but cannot create or mutate an OWNER account;
- OWNER can administer users; and
- a personal token can list and revoke only its own token records.

The existing `scripts/validate_rbac_http.py` exercises the same boundaries over
real Uvicorn HTTP in the validation container. No external data is collected.
