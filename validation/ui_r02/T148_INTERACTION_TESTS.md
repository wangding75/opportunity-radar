# T148 Interaction Tests

Result: PASS

- Source list links to source health with the real source id.
- Source health supports source-context filtering and shows circuit/failure fields returned by the API.
- Monitoring plan is read-only and shows the actual planner response shape.
- Run list links to detail with real run ids.
- Run detail is loaded from the existing collection-runs read endpoint and omits sensitive stack traces.
- Empty, error, degraded, circuit-open, and failed-run values are rendered as data/status states rather than fake recovery controls.
