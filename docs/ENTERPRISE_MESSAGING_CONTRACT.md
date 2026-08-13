# Enterprise messaging connector contract

T115-01 defines the provider-neutral boundary used by Mock, Slack, Feishu, and WeCom adapters.

`EnterpriseMessageRequest` contains a versioned `message_id`, stable `idempotency_key`, provider, opaque destination, plain text, optional provider-neutral blocks, data class, and audit-safe metadata. The request contract does not accept provider credentials. Adapter-specific destination and credential validation stays in the adapter boundary.

`EnterpriseMessageResult` must explicitly report `SENT`, `ACCEPTED`, `RETRYABLE_FAILURE`, `PERMANENT_FAILURE`, `SUPPRESSED`, or `INVALID`; a provider exception is never a success. Failure kinds distinguish transient provider errors, rate limits, authentication, invalid destinations, and policy blocks. `message_input_signature` is canonical and excludes the attempt counter, so retry attempts retain the same idempotency identity.

The default retry policy is bounded to five attempts with exponential backoff (60 seconds to one hour). All test fixtures in this contract use `SYNTHETIC` or `MOCK` data. The next adapter tasks may implement transport details without changing this core contract.
