# Risk escalation contract

`risk-escalation-v1` classifies a validated 0–100 risk score into stable
levels: `NONE` (<20), `LOW` (20–<40), `MEDIUM` (40–<60), `HIGH` (60–<80), and
`CRITICAL` (80–100). The boundaries are policy-configurable but must remain
non-decreasing.

An evaluation compares two persisted risk snapshots for the same opportunity
and model version. It reports `ESCALATED`, `DE_ESCALATED`, or `STABLE`; missing
baselines, model changes, out-of-order snapshots, and excessive lookback gaps
are explicit fail-closed states. An escalation occurs when the level rises or
both absolute and relative policy thresholds pass. Every result carries its
contract/algorithm/policy versions, time bounds, reasons, and a stable input
signature that does not depend on evaluation time.

The contract is domain-only in T112-01. Detection, evidence persistence,
AlertEvent delivery, replay, and MOCK/SYNTHETIC acceptance are owned by the
subsequent T112 tasks.
