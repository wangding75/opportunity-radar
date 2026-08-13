"""Docker-runnable HTTP Mock Mail Service with explicit MOCK semantics."""

from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException, Query

from app.domain.email_delivery import EmailDeliveryRequest
from app.services.mock_mail import MOCK_MAIL_VERSION, MockMailService

app = FastAPI(title="Opportunity Radar Mock Mail Service", version=MOCK_MAIL_VERSION)
mail = MockMailService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "provider": "mock-mail", "data_class": "MOCK", "version": MOCK_MAIL_VERSION}


@app.post("/v1/send")
def send(request: EmailDeliveryRequest, x_mock_failure: str | None = Header(default=None)) -> dict:
    if x_mock_failure:
        failure_mode = x_mock_failure.strip().lower()
        request = request.model_copy(update={"metadata": {**request.metadata, "_mock_failure": failure_mode}})
    result = mail.send(request)
    return {"data_class": "MOCK", "result": result.model_dump(mode="json")}


@app.get("/v1/messages")
def messages(limit: int = Query(default=100, ge=1, le=500)) -> list[dict]:
    return mail.messages(limit=limit)


@app.post("/v1/reset")
def reset() -> dict[str, str]:
    mail.reset()
    return {"status": "reset", "data_class": "MOCK"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("MOCK_MAIL_PORT", "8082")))
