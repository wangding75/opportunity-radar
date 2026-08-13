# Keyword burst contract

T107-01 defines `keyword-burst-v1` as a bounded, deterministic domain
evaluation. The detector uses half-open UTC windows: the current window ends at
`window_end`, and the immediately preceding baseline ends at the current start.
Missing days are explicitly zero-filled.

The default policy compares 7 current days with 28 baseline days. A non-new
burst must meet all thresholds: minimum current observations, absolute delta,
growth rate, z-score over the baseline daily distribution, and current source
support. A zero-observation baseline is classified as `NEW_SIGNAL` and only
passes when `include_new_signals` and the current observation/source minimums
are satisfied. Empty input therefore fails closed.

Every evaluation records the policy, contract/algorithm versions, window
boundaries, counts, means, standard deviation, growth, delta, z-score,
comparison, reasons, UTC evaluation time, and a SHA-256 input signature. The
signature includes both observation and source points plus policy, so changing
either input cannot reuse a prior decision. `current_sources` is a conservative
maximum daily source count because this contract receives counts rather than
source identities; source-independent confirmation remains a later task.

This task defines the contract only. T107-02 consumes it for persisted burst
detection, and T107-03 binds anomalous evaluations to evidence and alert
events.
