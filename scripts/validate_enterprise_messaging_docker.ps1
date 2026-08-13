$ErrorActionPreference = "Stop"

# T115-05 acceptance: exercise the provider-neutral HTTP adapter against the
# Compose-only MOCK Enterprise Messaging service using one SYNTHETIC message.
$project = "opportunity-radar-enterprise-acceptance"
$composeFiles = @("-f", "docker-compose.yml", "-f", "docker-compose.dev.yml")
$env:MOCK_ENTERPRISE_MESSAGING_HOST_PORT = "18084"

try {
    docker compose -p $project @composeFiles up -d mock-enterprise-messaging
    $health = Invoke-RestMethod "http://localhost:18084/health"
    if ($health.data_class -ne "MOCK" -or $health.contract_version -ne "enterprise-messaging-v1") {
        throw "Mock Enterprise Messaging health contract is invalid"
    }
    Invoke-RestMethod -Method Post "http://localhost:18084/v1/reset" | Out-Null

    $code = @'
import json
from app.domain.enterprise_messaging import EnterpriseDataClass, EnterpriseMessageRequest
from app.services.mock_enterprise_messaging_http import MockEnterpriseMessagingHTTPConfig, MockEnterpriseMessagingHTTPService

request = EnterpriseMessageRequest.synthetic_alert(
    message_id="msg_docker_synthetic_1",
    idempotency_key="idem_docker_synthetic_1",
    provider="mock",
    destination="synthetic-channel",
    title="SYNTHETIC enterprise alert",
    text="SYNTHETIC Docker Enterprise Messaging acceptance",
    alert_event_id=1,
    event_key="docker-synthetic-enterprise-event",
    data_class=EnterpriseDataClass.SYNTHETIC,
)
adapter = MockEnterpriseMessagingHTTPService(MockEnterpriseMessagingHTTPConfig("http://mock-enterprise-messaging:8084"))
result = adapter.send(request)
print(json.dumps({"status": result.status.value, "data_class": request.data_class.value, "provider_message_id": result.provider_message_id}))
if result.status.value != "SENT":
    raise SystemExit("Mock Enterprise Messaging adapter did not return SENT")
'@
    $adapterResult = $code | docker compose -p $project @composeFiles run --rm --no-deps api python -
    if ($LASTEXITCODE -ne 0) {
        throw "adapter container failed: $adapterResult"
    }
    Write-Output $adapterResult

    $messages = Invoke-RestMethod "http://localhost:18084/v1/messages"
    if ($messages.Count -ne 1 -or $messages[0].data_class -ne "MOCK" -or $messages[0].message_data_class -ne "SYNTHETIC") {
        throw "expected one MOCK/SYNTHETIC enterprise message, got $($messages.Count)"
    }
    Write-Output "PASS: Docker adapter delivered one SYNTHETIC message to the MOCK Enterprise Messaging service."
}
finally {
    docker compose -p $project @composeFiles down -v --remove-orphans
}
