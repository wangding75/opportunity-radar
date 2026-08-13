# Weekly trend persistence

T105-03 stores one versioned report per complete UTC week in
`weekly_trend_reports`. The row keeps the Monday-to-Monday report and baseline
boundaries, contract and algorithm versions, policy, generated time, status,
bounded candidate counts, and the input signature used to reproduce the result.

The JSON payload round-trips the complete `WeeklyTrendReport`. The separate
`explanation` field is an audit-friendly projection of every selected keyword's
comparison, delta, growth rate, stable trend signature, evidence provenance,
and selection reasons. It also keeps report warnings and generation errors, so
an empty or degraded result is distinguishable from a missing report.

Endpoints:

- `GET /api/v1/trends/weekly` returns the latest persisted report; pass
  `week_start=YYYY-MM-DD` to query a specific complete week.
- `GET /api/v1/trends/weekly/{week_start}` returns a specific persisted report.
- `POST /api/v1/trends/weekly/generate?anchor_date=YYYY-MM-DD` generates and
  idempotently persists the previous complete week. Generation requires the
  existing admin RBAC boundary.
- `GET /api/v1/exports/trends/weekly.csv` exports the latest report as a
  formula-neutralized CSV, including provenance, trend signatures, and
  selection reasons. Pass `week_start=YYYY-MM-DD` for a specific week.

The Dashboard renders the persisted report and exposes admin-only generation;
the read-only CSV export remains available to authenticated readers. The
`trends-weekly` Compose worker runs the same generator with the existing
heartbeat and migration dependencies, and its default interval is seven days.

All test fixtures are synthetic or explicitly marked mock data. No external
source is collected by this persistence task.
