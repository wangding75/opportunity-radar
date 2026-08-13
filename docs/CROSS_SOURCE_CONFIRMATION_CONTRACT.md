# Cross-source confirmation contract

T110-01 defines `cross-source-confirmation-v1` as a conservative, versioned domain decision. The input is a subject key plus bounded evidence citations. The output records the evaluation time, policy version, fresh/stale/future counts, deduplicated evidence IDs, independent endpoint count, unique claim count, reasons, and a stable input signature.

An independent endpoint is the normalized hostname from the evidence URL; all paths on one host, including `www.` aliases, remain one endpoint. When no valid hostname exists, the normalized source ID is used. This intentionally under-counts independence when source identity is ambiguous. Evidence claims are fingerprinted from normalized title/text without source or URL, so syndicated copies across two hosts do not satisfy confirmation on their own.

The default policy requires two fresh independent endpoints and two unique claims. Exact evidence-ID duplicates and syndicated claim duplicates are collapsed. Evidence exactly at the age cutoff is accepted; stale or future evidence is excluded. Empty or time-filtered input returns `NO_EVIDENCE`; insufficient endpoint/claim diversity returns `INSUFFICIENT_EVIDENCE`. No alert side effect is produced by this domain contract; later tasks own persistence and delivery.

All IDs use the existing `ev1_<sha256>` citation contract. Production callers must provide stored evidence; tests use explicitly marked `MOCK`/`SYNTHETIC` evidence only.
