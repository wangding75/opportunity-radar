# Score Jump contract

`score-jump-v1` compares two persisted opportunity score snapshots. Both
absolute and relative movement must pass: the defaults are at least 15 score
points and at least 25% relative growth. A score decrease or a change that
passes only one threshold is `NO_JUMP`.

The comparison is version-bound. By default the snapshots must refer to the
same opportunity, the same scoring model version, and a strictly increasing
calculation time within a 90-day bounded gap. Missing history is
`NO_BASELINE`; model changes are `VERSION_MISMATCH`; mismatched or out-of-order
snapshots are `INVALID_SEQUENCE`. These states never become positive alert
signals.

The output includes both snapshot versions/times, scores, deltas, policy and
algorithm versions, reasons, and a stable input signature that excludes only
the evaluation wall-clock time. Tests use explicitly marked `SYNTHETIC`
breakdowns and no external data.
