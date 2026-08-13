# Functional audit coverage report

This report separates matrix/static evidence from runtime, real PostgreSQL, external-integration and production-readiness evidence.
A static PASS is not functional completion. A row advances only when evidence is recorded in `validation/functional_validation_evidence.json`.

- Report integrity status: **PASS**
- Production readiness: **NOT_READY**
- Matrix rows / traceability entries: **30 / 30**
- Functional chain gaps: **0**
- Unregistered important implementation targets: **5**
- Real data collected for validation: **0**
- Data classes: **MOCK=7, SYNTHETIC=23**

## Validation layers

| Layer | Status | Evidence sources |
| --- | --- | --- |
| static_completion_hygiene | `PASS` | `validation/false_completion_scan.json` |
| runtime_functional_validation | `NOT_CHECKED` | none recorded |
| real_postgresql_validation | `RUNTIME_VERIFIED` | `validation/postgres_runtime_e2e_evidence.json` |
| external_integration_validation | `NOT_CHECKED` | none recorded |
| production_readiness | `NOT_READY` | none recorded |

Production readiness reasons:
- runtime functional evidence is not recorded
- external integration evidence is not recorded with real data

## Chain coverage

| Link | Rows with a real target |
| --- | ---: |
| code | 30 / 30 |
| api | 27 / 30 |
| ui | 22 / 30 |
| worker | 26 / 30 |
| tests | 30 / 30 |
| docs | 30 / 30 |

## Area coverage

| Area | Rows | Coverage statuses | Data classes |
| --- | ---: | --- | --- |
| Alert | 7 | STATIC_ONLY=7 | MOCK=1, SYNTHETIC=6 |
| Delivery | 4 | STATIC_ONLY=4 | MOCK=2, SYNTHETIC=2 |
| Enterprise | 4 | STATIC_ONLY=4 | MOCK=2, SYNTHETIC=2 |
| Graph | 1 | STATIC_ONLY=1 | SYNTHETIC=1 |
| Keyword | 2 | STATIC_ONLY=2 | SYNTHETIC=2 |
| Observation | 3 | STATIC_ONLY=3 | MOCK=1, SYNTHETIC=2 |
| Operations | 3 | STATIC_ONLY=3 | SYNTHETIC=3 |
| Opportunity | 3 | STATIC_ONLY=3 | MOCK=1, SYNTHETIC=2 |
| Security | 2 | STATIC_ONLY=2 | SYNTHETIC=2 |
| Trend | 1 | STATIC_ONLY=1 | SYNTHETIC=1 |

## Reverse coverage findings

The following important API modules, connectors, core services or workers are not registered by a matrix traceability entry. This is an explicit review finding, not a hidden success state.

| Kind | Target | Reason |
| --- | --- | --- |
| api_module | `backend/app/api/scoring.py` | important implementation target is not referenced by any functional matrix traceability entry |
| connector | `backend/app/connectors/instrumented_app.py` | important implementation target is not referenced by any functional matrix traceability entry |
| core_service | `backend/app/services/dashboard.py` | important implementation target is not referenced by any functional matrix traceability entry |
| core_service | `backend/app/services/digest.py` | important implementation target is not referenced by any functional matrix traceability entry |
| core_service | `backend/app/services/digest_persistence.py` | important implementation target is not referenced by any functional matrix traceability entry |

## Explicit N/A exceptions

These are intentional backend-only, internal-contract or isolated-Mock links; they are not counted as functional chain gaps.

| Trace ID | Link | Reason |
| --- | --- | --- |
| FM-OPP-003 | worker_targets | N/A - human-owned research state is changed synchronously by the API |
| FM-DEL-001 | ui_targets | N/A - email delivery is a backend queue capability; its durable records are exposed by the API |
| FM-DEL-002 | ui_targets | N/A - webhook delivery is a backend queue capability; endpoint and delivery records are exposed by the API |
| FM-DEL-003 | ui_targets | N/A - security policy is enforced before backend delivery and is covered by API tests |
| FM-DEL-004 | ui_targets | N/A - Mock Webhook receiver is an isolated verification service |
| FM-DEL-004 | worker_targets | N/A - the receiver is an isolated HTTP service; the product worker is mapped under FM-DEL-002 |
| FM-ENT-001 | api_targets | N/A - provider-neutral contract is an internal delivery port, not a public product endpoint |
| FM-ENT-001 | ui_targets | N/A - provider-neutral contract is consumed by backend delivery |
| FM-ENT-002 | ui_targets | N/A - Mock Enterprise Messaging is an isolated verification service |
| FM-ENT-002 | worker_targets | N/A - the Mock service is isolated; product worker integration is mapped under FM-ENT-004 |
| FM-ENT-003 | api_targets | N/A - Slack, Feishu and WeCom adapters are internal provider ports |
| FM-ENT-003 | ui_targets | N/A - provider adapter payloads are backend-only |
| FM-ENT-004 | api_targets | N/A - routing is invoked by the delivery worker; no public product endpoint is required |
| FM-ENT-004 | ui_targets | N/A - routing templates and fallback traces are backend delivery records |
| FM-SEC-001 | worker_targets | N/A - authorization is enforced synchronously at the API boundary |

## Evidence rows

| Trace ID | Area | Capability | Coverage status | Data | Evidence sources |
| --- | --- | --- | --- | --- | --- |
| FM-OBS-001 | Observation | bounded source collection and raw observation persistence | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-OBS-002 | Observation | feed, GitHub and Google Trends connector boundaries | `STATIC_ONLY` | `MOCK` | `validation/false_completion_scan.json` |
| FM-OBS-003 | Observation | source health, circuit and retry state | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-KEY-001 | Keyword | keyword normalization, aliases and quality | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-KEY-002 | Keyword | keyword quality and evidence trace | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-TRE-001 | Trend | weekly trend contract, aggregation and persistence | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-GRA-001 | Graph | opportunity clusters, lineage and graph relations | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-OPP-001 | Opportunity | opportunity scoring and evidence breakdown | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-OPP-002 | Opportunity | provider analysis queue and citations | `STATIC_ONLY` | `MOCK` | `validation/false_completion_scan.json` |
| FM-OPP-003 | Opportunity | research workflow and human-owned state | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-ALT-001 | Alert | alert rule evaluation and event lifecycle | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-ALT-002 | Alert | high-signal alert eligibility and acceptance | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-ALT-003 | Alert | keyword burst detection, evidence and replay | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-ALT-004 | Alert | new tool/product normalization and alerts | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-ALT-005 | Alert | hiring surge detector and mock replay | `STATIC_ONLY` | `MOCK` | `validation/false_completion_scan.json` |
| FM-ALT-006 | Alert | cross-source confirmation and independence | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-ALT-007 | Alert | score jump and risk escalation explanations | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-DEL-001 | Delivery | versioned email contract and durable queue | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-DEL-002 | Delivery | versioned Webhook contract, endpoint and queue | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-DEL-003 | Delivery | Webhook SSRF, DNS and signature boundary | `STATIC_ONLY` | `MOCK` | `validation/false_completion_scan.json` |
| FM-DEL-004 | Delivery | Mock Webhook receiver verification and idempotency | `STATIC_ONLY` | `MOCK` | `validation/false_completion_scan.json` |
| FM-ENT-001 | Enterprise | unified enterprise messaging contract | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-ENT-002 | Enterprise | Mock Enterprise Messaging service | `STATIC_ONLY` | `MOCK` | `validation/false_completion_scan.json` |
| FM-ENT-003 | Enterprise | Slack/Feishu/WeCom adapter payload boundary | `STATIC_ONLY` | `MOCK` | `validation/false_completion_scan.json` |
| FM-ENT-004 | Enterprise | versioned templates, routing and degradation | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-SEC-001 | Security | RBAC, CSRF, token and admin boundary | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-SEC-002 | Security | request audit and request/trace correlation | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-OPS-001 | Operations | worker heartbeat, leases and observability metrics | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-OPS-002 | Operations | probe scheduler and worker mode boundaries | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |
| FM-OPS-003 | Operations | migration, backup/restore and product hardening | `STATIC_ONLY` | `SYNTHETIC` | `validation/false_completion_scan.json` |

The complete file-level targets and evidence-derived statuses are in `validation/functional_audit_report.json`. The current matrix policy permits only SYNTHETIC or MOCK validation data; it does not establish production readiness.
