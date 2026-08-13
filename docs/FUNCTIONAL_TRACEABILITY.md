# Functional traceability

`validation/functional_traceability.json` is the executable evidence map for the
30 rows in `validation/functional_matrix.json`. Every `trace_id` has one entry
covering:

- real implementation files in `code_targets`;
- product routes or an explicit `N/A - ...` explanation in `api_targets`;
- served/source UI files or an explicit backend-only explanation in `ui_targets`;
- worker files or an explicit synchronous/backend-only explanation in `worker_targets`;
- test files and documentation files that exist in the repository; and
- a short evidence statement describing the contract and state transition.

The mapping is intentionally path-based so it can be audited without importing
the application or contacting an external provider. Product `/api/v1/...`
targets are checked against the route decorators in `backend/app/api`; isolated
Mock service routes remain separate from the product API. `N/A` is only accepted
when the capability is a domain contract, adapter, isolated receiver, or
backend-only queue with no user-facing route.

Run the validator directly:

```text
python scripts/validate_traceability.py
```

The product validation script and the regression test suite run the same check.
All evidence data classes remain `SYNTHETIC` or `MOCK`; no live provider data is
required.
