# Functional matrix gap scan

`scripts/scan_functional_matrix_gaps.py` runs the matrix and traceability
validators, then checks the implementation chain for every trace ID:

- code, test and documentation evidence may never be entirely `N/A`;
- product capabilities must expose a real `/api/v1/...` route unless they are
  explicitly internal enterprise contracts;
- user-facing capabilities must point to the served/static UI and source UI;
- asynchronous capabilities must point to the production Worker unless the
  row is explicitly synchronous or an isolated Mock receiver/service.

The exceptions are named by trace ID in the scanner so a future N/A cannot hide
an accidental missing link. The scan uses only repository paths and the
SYNTHETIC/MOCK matrix; it does not contact providers or collect live data.

Run it with:

```text
python scripts/scan_functional_matrix_gaps.py
```

The product validation script and regression tests require a zero-gap result.
