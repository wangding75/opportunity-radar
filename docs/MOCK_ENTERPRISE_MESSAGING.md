# Mock Enterprise Messaging Service

T115-02 provides both an in-process `MockEnterpriseMessagingService` and a Docker-ready HTTP service implementing `enterprise-messaging-v1`.

- `POST /v1/send` accepts the provider-neutral request and returns a typed `EnterpriseMessageResult` under a top-level `data_class=MOCK` marker.
- `GET /v1/messages` exposes only bounded, synthetic/mock captures for acceptance inspection.
- `POST /v1/reset` clears the in-memory test state explicitly.
- Terminal results are idempotent by canonical input signature and do not append another message on repeat delivery.
- `_mock_failure=transient|rate_limited|permanent|blocked|suppressed` exercises explicit failure semantics; no failure is reported as `SENT`.

The HTTP adapter rejects unlabeled or malformed responses and maps transport/server failures to retryable results. No real enterprise provider or real business data is contacted.
