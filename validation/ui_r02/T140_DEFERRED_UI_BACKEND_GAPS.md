# T140 — Deferred UI/backend gaps

The audit found no safe need for a new backend business endpoint. The following prototype actions are intentionally deferred because the repository does not expose the capability without inventing semantics or changing deployment/worker behavior.

| Capability | Pages | UI treatment | Reason |
|---|---|---|---|
| Unified global search | P03 | Client-side aggregate of existing reads; unsupported categories omitted | No unified search contract exists |
| Opportunity archive/ignore/state write | P12/P13 | Hidden | No confirmed state-transition API beyond research state |
| Research workflow start/retry/cancel/step retry/export | P13–P17 | Read-only unavailable section / hidden actions | No research workflow persistence or mutation API |
| Source editor/test connection/enable-disable | P18/P19 | Read-only source registry; only confirmed preference write in P29-E | Connector configuration is deployment-owned |
| Monitoring pause/resume/run-now | P20 | Read-only probe/plan data | No safe planner mutation contract |
| Run retry | P21/P22 | Hidden | No run retry endpoint |
| Analysis queue retry | P23 | Read-only queue/analysis status | No queue mutation endpoint |
| Alert read/unread/mark-all-read | P24 | Read-only lifecycle status | Existing lifecycle supports acknowledged/dismissed/resolved, not inbox read state |
| Alert rule enable/disable/test/delete | P25 | Create/edit only where confirmed; unsupported controls hidden | No delete/test channel contract; enabled is exposed by rule write schema but no separate UI control is required |
| General/security/notification/integration settings | P29-A–D | Read-only or deferred section | No settings schema/API; deployment settings must not be made writable |
| Source preference restore default/reorder | P29-E | Hidden | Only `{enabled,note}` patch is confirmed |

These are safe deferred gaps, not execution blockers. The implementation contract and matrix are the source of truth for runtime guards.
