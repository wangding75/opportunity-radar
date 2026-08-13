# Tool/Product Entity Normalization

T108-02 materializes the T108-01 identification contract over normalized
observations. The normalizer is bounded to 500 normalized items per run and
uses the normalized title (falling back to the query) as the candidate name.
When an incremental run is supplied item IDs, it reloads matching titles across
all sources so a second source joins the existing `tp1_` identity.

Each decision is stored in `tool_product_normalization_runs`, including the
contract and algorithm versions, policy version, reasons, evidence IDs, input
signature, and evaluation time. Identified and low-confidence decisions are
upserted into `tool_product_entities`; their evidence is linked through
`tool_product_entity_evidence` using stable `ev1_` citation IDs. Unresolved and
insufficient decisions are retained as runs but never fabricate an entity.

The operation is idempotent on `input_signature`. Replaying unchanged evidence
therefore creates no additional run or evidence link. `POST
/api/v1/tool-products/normalize` is admin-only; entity reads are available to
authenticated readers. The import and derived-analysis paths invoke the same
service, so this is not a UI-only or API-only placeholder.

All tests use explicitly marked `MOCK`/`SYNTHETIC` evidence. No external data is
collected by this task.
