# Enterprise messaging Docker acceptance

Compose includes `mock-enterprise-messaging`, a local-only substitute for an unavailable Slack/Feishu/WeCom service. It exposes the same provider-neutral HTTP adapter boundary, reports `data_class=MOCK`, and stores only bounded in-memory MOCK captures.

Run:

```powershell
./scripts/validate_enterprise_messaging_docker.ps1
```

The script checks the Mock health contract, resets state, runs the application image as an adapter client, sends one `SYNTHETIC` message, and verifies one captured `MOCK` message. It uses no external network, credentials, or real enterprise data. Compose resources are removed on completion.
