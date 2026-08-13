# Functional matrix and traceability

`validation/functional_matrix.json` is the machine-readable T116-01 product matrix. Every row has a stable `FM-*` trace ID, one product capability, input/output/state semantics, a test target, and an explicit `SYNTHETIC` or `MOCK` data class.

Validate it independently with:

```powershell
python scripts/validate_functional_matrix.py
```

The product validation script runs the same check before the test suite. The validator rejects duplicate/invalid trace IDs, missing capability areas, missing test files, unsafe data classes, and TODO/FIXME placeholders. Runtime request/trace correlation IDs remain covered by the existing API audit middleware and are represented by `FM-SEC-002`.
