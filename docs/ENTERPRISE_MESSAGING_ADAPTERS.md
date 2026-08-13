# Enterprise messaging adapters

T115-03 implements provider boundaries over `EnterpriseMessagePort`:

- `SlackMessagingAdapter` emits Slack incoming-webhook JSON (`text`, optional `blocks`).
- `FeishuMessagingAdapter` emits Feishu bot text JSON (`msg_type=text`).
- `WeComMessagingAdapter` emits WeCom robot text JSON (`msgtype=text`).

Each adapter requires a matching `request.provider`, keeps endpoint credentials in its immutable config rather than the request contract, disables redirects, bounds timeouts to 1–120 seconds, and returns the same typed status/failure taxonomy. HTTP 408/425/429/5xx and transport errors are retryable; other HTTP failures are permanent. Feishu/WeCom HTTP-200 provider error bodies are also treated as failures.

Tests use `httpx.MockTransport` and SYNTHETIC messages only. Real provider URLs and credentials are not used.
