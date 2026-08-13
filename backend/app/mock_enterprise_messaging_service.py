"""Docker-runnable Mock Enterprise Messaging Service."""

from __future__ import annotations

import os

from fastapi import FastAPI, Header, Query

from app.domain.enterprise_messaging import EnterpriseMessageRequest
from app.services.mock_enterprise_messaging import MOCK_ENTERPRISE_MESSAGING_VERSION, MockEnterpriseMessagingService

app = FastAPI(title="Opportunity Radar Mock Enterprise Messaging Service", version=MOCK_ENTERPRISE_MESSAGING_VERSION)
messaging = MockEnterpriseMessagingService()


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "provider": "mock-enterprise-messaging",
        "data_class": "MOCK",
        "version": MOCK_ENTERPRISE_MESSAGING_VERSION,
        "contract_version": "enterprise-messaging-v1",
    }


@app.post("/v1/send")
def send(request: EnterpriseMessageRequest, x_mock_failure: str | None = Header(default=None)) -> dict:
    if x_mock_failure:
        request = request.model_copy(update={"metadata": {**request.metadata, "_mock_failure": x_mock_failure.strip().lower()}})
    result = messaging.send(request)
    return {"data_class": "MOCK", "result": result.model_dump(mode="json")}


@app.get("/v1/messages")
def messages(limit: int = Query(default=100, ge=1, le=500)) -> list[dict]:
    return messaging.messages(limit=limit)


@app.post("/v1/reset")
def reset() -> dict[str, str]:
    messaging.reset()
    return {"status": "reset", "data_class": "MOCK"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("MOCK_ENTERPRISE_MESSAGING_PORT", "8084")))
