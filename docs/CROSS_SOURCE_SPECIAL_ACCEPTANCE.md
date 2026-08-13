# Cross-source special acceptance

The T110-04 acceptance suite covers the failure-prone source cases that should
never silently become a positive alert:

- two independent endpoints with the same topic but contradictory text are
  recorded as a conflict and remain `INSUFFICIENT_EVIDENCE`;
- a domain input above the configured evidence bound is rejected before score
  calculation;
- several source IDs on one hostname remain one independent endpoint, so
  repeated pages cannot satisfy confirmation alone.

The fixtures are explicitly `SYNTHETIC` and contain no real external data.
Normal confirmation, persistence, rollback/retry, score, AlertEvent, ACK, and
RBAC paths remain covered by the preceding T110 tests.
