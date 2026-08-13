# Keyword, trend and graph audit

`backend/app/services/keyword_trend_graph_audit.py` audits the materialized
Keyword → TrendDaily → Graph chain. It verifies mention provenance and keyword
metrics, daily bucket counts/source diversity within the 90-day contract,
canonical graph pairs, item-level relation idempotency, relation/source counts,
and the documented graph weight formula.

Graph retries are protected by the `keyword_relation_items` table and its
unique `(keyword_a, keyword_b, relation_type, normalized_item)` key. Migration
`0029_keyword_relation_items` backfills idempotency markers for existing
relations without changing historical counts.

Run after migration with:

```text
python scripts/audit_keyword_trend_graph.py
```

The report is written to `validation/keyword_trend_graph_audit.json` and uses
only synthetic/mock validation data (`real_data_collected=0`).
