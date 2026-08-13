# Keyword burst detector

T107-02 implements `detect_keyword_bursts` over the existing
`KeywordTrendDaily` materialization. It reads only the bounded baseline/current
window from the T107-01 contract, zero-fills missing days in the Domain layer,
and returns a versioned evaluation for every selected keyword. The detector is
read-only and has a hard limit of 500 keywords per call.

`detect_anomalous_keyword_bursts` is a convenience filter over the same result;
it does not create alert events or mutate human research state. Repeating a
call with the same database snapshot, window end, and policy produces the same
input signature and no duplicate side effect. T107-03 consumes anomalous
evaluations to bind evidence and alert lifecycle records.
