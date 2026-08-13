# Tool/Product Alerts and Mock Acceptance

T108-04 materializes `NEW_TOOL` alert events from `FIRST_SEEN` occurrences.
Every event is linked to `tool_product_entity_id` and back to the occurrence's
stable `ev1_` evidence ID. The message records the entity key, source,
observation time, input signature, contract version, and algorithm version, so
the alert can be audited without using database-local IDs as evidence identity.

The alert event key is the occurrence key. Re-running the worker or admin
endpoint therefore creates no duplicate event; a transaction rollback leaves
both the occurrence link and event available for a clean retry. Only
`IDENTIFIED` entities can produce occurrences and alerts. Low-confidence,
unresolved, and insufficient-evidence decisions fail closed.

`POST /api/v1/alerts/tool-products/evaluate` is admin-only and the regular
`alerts` worker mode invokes the same service. The existing alert lifecycle API
supports ACK/DISMISS/RESOLVE, and the frontend displays tool/product entity
context alongside the alert. Tests use only explicitly marked `MOCK` and
`SYNTHETIC` observations; no external provider or real data is used.
