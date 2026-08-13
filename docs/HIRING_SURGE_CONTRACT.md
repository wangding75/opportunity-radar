# Hiring Surge Contract

T109-01 defines `hiring-surge-v1` for bounded job-posting growth evaluation.
The current window is half-open and ends at `window_end`; the immediately
preceding baseline has the configured length. Missing days are zero-filled.
The default policy compares 7 current days with 28 baseline days and requires
minimum current jobs, absolute delta, growth rate, z-score, source support, and
raw-evidence support. A zero-job baseline is classified as `NEW_SIGNAL` and
only qualifies when the new-signal and current minimums pass. Empty input fails
closed.

Each evaluation records the contract/algorithm/policy versions, exact window
boundaries, job/source/evidence counts, means, standard deviation, growth,
delta, z-score, comparison, reasons, UTC evaluation time, and a SHA-256 input
signature over all daily inputs and policy. Later detector and alert tasks must
retain this output and bind any alert to raw job evidence.

Tests use only `MOCK`/`SYNTHETIC`-labelled contract inputs. No external data is
collected by this task.
