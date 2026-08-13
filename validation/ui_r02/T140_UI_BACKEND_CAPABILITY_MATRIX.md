# T140 — R02 UI ↔ backend capability matrix

Status: **PASS**. All 34 screens and every metadata action are covered below. `MATCHED` means a current API or browser capability is bound; `UI_ONLY` means no backend call is needed; `DEFERRED_UNAVAILABLE` is intentionally guarded by the deferred registry.

| Screen | Required capability groups | Resolved contract | Classification | UI handling |
|---|---|---|---|---|
| P01 | login, password visibility | POST `/api/v1/auth/login` | MATCHED/UI_ONLY | Real session, 401/429/service error |
| P02 | dashboard refresh, navigation, global search | GET `/api/v1/dashboard` | MATCHED/UI_ONLY | Composed cards; partial sections retain shell |
| P03 | search, clear/filter, result navigation | Existing `/opportunities/page`, `/observations`, `/keywords`, `/opportunities` | MATCHED/UI_ONLY | Client aggregate; no invented unified API |
| P04 | forbidden, back/dashboard | browser/router | UI_ONLY | Distinct 403 state |
| P05 | not-found, back/context list | browser/router | UI_ONLY | Distinct 404 state |
| P06 | observation read/query/external source | GET `/api/v1/observations` | MATCHED/UI_ONLY | Read-only table, cursor query |
| P07 | observation detail links/source | list payload + route context | MATCHED/UI_ONLY | Safe `http(s)` external links only |
| P08 | keyword discovery/watch conditional/links | GET `/api/v1/keywords`; watch APIs | MATCHED/DEFERRED | Watch action uses confirmed schema; unsupported variants hidden |
| P09 | watch keyword CRUD/toggle | GET/POST/PATCH `/api/v1/watch-keywords` | MATCHED/UI_ONLY | Actual fields only |
| P10 | trend window/evidence/graph/opportunity | GET `/api/v1/keywords/{id}/trend` or weekly report | MATCHED/UI_ONLY | Supported parameters only |
| P11 | graph read/canvas/node links | GET `/api/v1/keyword-graph` | MATCHED/UI_ONLY | Client canvas interactions |
| P12 | opportunity list/query/export/state | GET `/api/v1/opportunities/page`; export CSV | MATCHED/DEFERRED | Export when endpoint is confirmed; state writes hidden |
| P13 | detail/research/evidence/analysis links | GET detail; PATCH research | MATCHED/DEFERRED | Research state only; workflow/state actions guarded |
| P14 | structured analysis/read/trigger/research | GET opportunity detail; provider read | MATCHED/DEFERRED | Actual analysis fields; trigger controls hidden |
| P15 | workflow list/result/retry/cancel | no workflow API | DEFERRED_UNAVAILABLE/UI_ONLY | Read-only unavailable section; no fake rows/actions |
| P16 | workflow detail/result/step retry | no workflow API | DEFERRED_UNAVAILABLE/UI_ONLY | Safe deferred section |
| P17 | research result/evidence/export | no workflow result API | DEFERRED_UNAVAILABLE/UI_ONLY | Traceable empty/deferred state |
| P18 | source list/editor/test/toggle | GET sources/health; preference only | MATCHED/DEFERRED | Registry read-only; config actions hidden |
| P19 | source health/edit/test/toggle/runs | GET `/sources/health` | MATCHED/DEFERRED | Health/read-only and links |
| P20 | monitoring plan/pause/run-now | GET `/probes/plan` and tasks | MATCHED/DEFERRED | Plan read-only; mutations hidden |
| P21 | run list/query/retry | GET `/collection-runs` | MATCHED/DEFERRED | Read-only run list; retry hidden |
| P22 | run detail/links/retry/copy ID | run list record | MATCHED/DEFERRED/UI_ONLY | Safe detail/copy; retry hidden |
| P23 | analysis queue/retry/links | opportunity analysis statuses | MATCHED/DEFERRED | Read-only queue derived from real rows |
| P24 | alert inbox/detail/links/read state | GET/PATCH alert events | MATCHED/DEFERRED | Lifecycle actions only; read-state hidden |
| P25 | rule list/create/edit/toggle/test/delete | GET/POST/PATCH alert rules | MATCHED/DEFERRED | Schema-driven create/edit; unsupported actions hidden |
| P26 | audit read/filter/detail/copy | GET `/api/v1/audit` | MATCHED/UI_ONLY | Admin read-only |
| P27 | users/edit/OWNER confirm/create | admin user APIs | MATCHED/UI_ONLY | Server OWNER invariant authoritative |
| P28 | password/session/token/logout | token/auth APIs; password change absent | MATCHED/DEFERRED | Token/logout real; password/session revoke guarded |
| P29-A | settings general/save | no settings API | DEFERRED_UNAVAILABLE/UI_ONLY | Deployment-owned read-only section |
| P29-B | settings security/save | no settings API | DEFERRED_UNAVAILABLE/UI_ONLY | No secret/config mutation |
| P29-C | notification save/test/toggle | no settings API | DEFERRED_UNAVAILABLE/UI_ONLY | Deferred channel section |
| P29-D | integration save/test/toggle | webhook read/write exists, generic integrations absent | DEFERRED_UNAVAILABLE | Only confirmed webhook surfaces may appear |
| P29-E | source preference/save/restore/reorder | PATCH `/api/v1/sources/{id}/preference` | MATCHED/DEFERRED | Enabled/note only; restore/reorder hidden |
| P30 | health/readiness/diagnostics/links | GET `/health`, `/ready`, read endpoints | MATCHED/UI_ONLY | Read-only partial diagnostics |

Detailed route, request/response, auth and permission evidence is preserved in `docs/ui-r02/RESOLVED_UI_BACKEND_BINDINGS.json` and the live FastAPI route inventory generated by the backend tests.
