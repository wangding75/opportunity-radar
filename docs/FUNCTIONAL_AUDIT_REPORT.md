# Functional audit coverage report

This deterministic report is generated from the functional matrix, the implementation traceability map and the zero-gap scanner.

- Status: **PASS**
- Matrix rows / traceability entries: **30 / 30**
- Areas: **10**
- Functional gaps: **0**
- Real data collected for validation: **0**
- Data classes: **MOCK=7, SYNTHETIC=23**

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

| Area | Rows | Complete | Data classes |
| --- | ---: | ---: | --- |
| Alert | 7 | 7 | MOCK=1, SYNTHETIC=6 |
| Delivery | 4 | 4 | MOCK=2, SYNTHETIC=2 |
| Enterprise | 4 | 4 | MOCK=2, SYNTHETIC=2 |
| Graph | 1 | 1 | SYNTHETIC=1 |
| Keyword | 2 | 2 | SYNTHETIC=2 |
| Observation | 3 | 3 | MOCK=1, SYNTHETIC=2 |
| Operations | 3 | 3 | SYNTHETIC=3 |
| Opportunity | 3 | 3 | MOCK=1, SYNTHETIC=2 |
| Security | 2 | 2 | SYNTHETIC=2 |
| Trend | 1 | 1 | SYNTHETIC=1 |

## Explicit N/A exceptions

These are intentional backend-only, internal-contract or isolated-Mock links; they are not counted as functional gaps.

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

| Trace ID | Area | Capability | State | Data | Test evidence |
| --- | --- | --- | --- | --- | --- |
| FM-OBS-001 | Observation | bounded source collection and raw observation persistence | `collected_or_source_failed` | `SYNTHETIC` | `backend/tests/test_signal_engine.py` |
| FM-OBS-002 | Observation | feed, GitHub and Google Trends connector boundaries | `success_or_degraded` | `MOCK` | `backend/tests/test_feed_connector.py`, `backend/tests/test_github_connector.py`, `backend/tests/test_google_trends_connector.py` |
| FM-OBS-003 | Observation | source health, circuit and retry state | `healthy_degraded_circuit_open` | `SYNTHETIC` | `backend/tests/test_source_health.py` |
| FM-KEY-001 | Keyword | keyword normalization, aliases and quality | `normalized_or_rejected` | `SYNTHETIC` | `backend/tests/test_keyword_logic.py` |
| FM-KEY-002 | Keyword | keyword quality and evidence trace | `accepted_or_low_quality` | `SYNTHETIC` | `backend/tests/test_keyword_quality.py` |
| FM-TRE-001 | Trend | weekly trend contract, aggregation and persistence | `complete_or_empty` | `SYNTHETIC` | `backend/tests/test_weekly_trend_persistence.py` |
| FM-GRA-001 | Graph | opportunity clusters, lineage and graph relations | `stable_or_merged` | `SYNTHETIC` | `backend/tests/test_opportunity_clusters.py` |
| FM-OPP-001 | Opportunity | opportunity scoring and evidence breakdown | `scored_or_degraded` | `SYNTHETIC` | `backend/tests/test_signal_engine.py` |
| FM-OPP-002 | Opportunity | provider analysis queue and citations | `analyzed_pending_degraded` | `MOCK` | `backend/tests/test_analysis_queue.py`, `backend/tests/test_opportunity_analysis_provider.py` |
| FM-OPP-003 | Opportunity | research workflow and human-owned state | `starred_notes_tags_preserved` | `SYNTHETIC` | `backend/tests/test_product_workflow.py` |
| FM-ALT-001 | Alert | alert rule evaluation and event lifecycle | `new_acknowledged_dismissed_resolved` | `SYNTHETIC` | `backend/tests/test_alert_lifecycle.py` |
| FM-ALT-002 | Alert | high-signal alert eligibility and acceptance | `eligible_suppressed_duplicate` | `SYNTHETIC` | `backend/tests/test_high_signal_alert_acceptance.py`, `backend/tests/test_high_signal_alerts.py` |
| FM-ALT-003 | Alert | keyword burst detection, evidence and replay | `anomalous_or_no_data` | `SYNTHETIC` | `backend/tests/test_keyword_burst_replay.py`, `backend/tests/test_keyword_burst_detector.py` |
| FM-ALT-004 | Alert | new tool/product normalization and alerts | `first_seen_duplicate_alerted` | `SYNTHETIC` | `backend/tests/test_tool_product_alerts.py`, `backend/tests/test_tool_product_occurrences.py` |
| FM-ALT-005 | Alert | hiring surge detector and mock replay | `surge_or_no_evidence` | `MOCK` | `backend/tests/test_hiring_surge_mock_acceptance.py`, `backend/tests/test_hiring_surge_detector.py` |
| FM-ALT-006 | Alert | cross-source confirmation and independence | `confirmed_insufficient_suppressed` | `SYNTHETIC` | `backend/tests/test_cross_source_special_acceptance.py`, `backend/tests/test_cross_source_confirmations.py` |
| FM-ALT-007 | Alert | score jump and risk escalation explanations | `jump_escalated_duplicate` | `SYNTHETIC` | `backend/tests/test_risk_escalation_records.py`, `backend/tests/test_score_jump_breakdown.py`, `backend/tests/test_score_jump_alerts.py` |
| FM-DEL-001 | Delivery | versioned email contract and durable queue | `queued_claimed_retry_sent` | `SYNTHETIC` | `backend/tests/test_email_delivery_queue.py`, `backend/tests/test_email_delivery_contract.py` |
| FM-DEL-002 | Delivery | versioned Webhook contract, endpoint and queue | `queued_retry_sent_invalid` | `SYNTHETIC` | `backend/tests/test_webhook_delivery_queue.py`, `backend/tests/test_webhook_contract.py` |
| FM-DEL-003 | Delivery | Webhook SSRF, DNS and signature boundary | `accepted_or_blocked` | `MOCK` | `backend/tests/test_webhook_security.py` |
| FM-DEL-004 | Delivery | Mock Webhook receiver verification and idempotency | `accepted_duplicate_rejected` | `MOCK` | `backend/tests/test_mock_webhook_service.py` |
| FM-ENT-001 | Enterprise | unified enterprise messaging contract | `sent_retryable_permanent` | `SYNTHETIC` | `backend/tests/test_enterprise_messaging_contract.py` |
| FM-ENT-002 | Enterprise | Mock Enterprise Messaging service | `sent_duplicate_failure` | `MOCK` | `backend/tests/test_mock_enterprise_messaging.py` |
| FM-ENT-003 | Enterprise | Slack/Feishu/WeCom adapter payload boundary | `sent_retryable_invalid` | `MOCK` | `backend/tests/test_enterprise_messaging_adapters.py` |
| FM-ENT-004 | Enterprise | versioned templates, routing and degradation | `sent_degraded_retryable_no_route` | `SYNTHETIC` | `backend/tests/test_enterprise_messaging_routing.py` |
| FM-SEC-001 | Security | RBAC, CSRF, token and admin boundary | `allowed_or_denied` | `SYNTHETIC` | `backend/tests/test_product_security.py` |
| FM-SEC-002 | Security | request audit and request/trace correlation | `audited_or_rejected` | `SYNTHETIC` | `backend/tests/test_api.py` |
| FM-OPS-001 | Operations | worker heartbeat, leases and observability metrics | `running_idle_error_stale` | `SYNTHETIC` | `backend/tests/test_observability.py` |
| FM-OPS-002 | Operations | probe scheduler and worker mode boundaries | `claimed_completed_retry` | `SYNTHETIC` | `backend/tests/test_probe_scheduler.py` |
| FM-OPS-003 | Operations | migration, backup/restore and product hardening | `upgraded_restored_rejected` | `SYNTHETIC` | `backend/tests/test_product_hardening.py` |

The complete file-level code/API/UI/Worker/test/document targets are in `validation/functional_audit_report.json`. All rows use SYNTHETIC or MOCK validation data.
