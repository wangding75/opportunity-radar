# Analysis provider mock and observability

The `mock-analysis` Compose service implements the same HTTP contract consumed
by `HttpOpportunityAnalyzer`:

- `POST /v1/analyze` accepts `schema_version`, `citation_contract_version`, and
  the bounded `opportunity` payload.
- The payload must contain at least one valid `ev1_<sha256>` evidence ID.
- The response returns all five structured analysis fields plus citations bound
  to the input evidence IDs.
- Every response is explicitly marked `data_class: MOCK` and includes an
  `analysis_version`, `generated_at`, and deterministic `input_signature`.
- `GET /health` exposes the service status and mock version.

Start the service with `docker compose up -d mock-analysis`. From the API or
worker containers, configure `ANALYSIS_PROVIDER=http` and
`ANALYSIS_HTTP_ENDPOINT=http://mock-analysis:8080/v1/analyze` to exercise the
adapter without contacting an external provider. The host-only port defaults
to `127.0.0.1:8081`.

For deterministic failure tests, send `X-Mock-Failure: true`; the service
returns HTTP 503 and never fabricates a successful result. Empty evidence,
invalid evidence IDs, unsupported contract versions, and oversized input are
rejected with HTTP 422.

The application `/metrics` endpoint exposes these provider counters:

- `opportunity_radar_analysis_provider_calls_total`
- `opportunity_radar_analysis_provider_retries_total`
- `opportunity_radar_analysis_provider_fallbacks_total`
- `opportunity_radar_analysis_provider_selections_total`
- `opportunity_radar_analysis_provider_conflicts_total`

No real external data is required for this validation path; all mock evidence
must remain explicitly `MOCK` or `SYNTHETIC`.
