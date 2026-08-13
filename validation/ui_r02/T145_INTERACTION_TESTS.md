# T145 Interaction Tests

Result: PASS

| Case | Expected |
|---|---|
| Observation filter submit | Live API request with q/source_id/item_type |
| Observation next/previous | Offset changes without leaving P06 |
| Observation no-result | Empty/no-result panel |
| Observation detail missing id | Safe object-not-found state |
| Keyword discovery row | Navigates to trend with keyword_id |
| Watch keyword add | POST uses confirmed keyword/priority/notes fields |
| Watch keyword toggle | PATCH uses confirmed enabled field and reloads |
| Trend missing keyword | Browse link to P08 |
| Trend data | Persisted 7d/30d/90d windows and points only |
