from __future__ import annotations

from app.domain.enums import AcquisitionMethod, AcquisitionRisk, Capability, EvidenceQuality, QueryMode
from app.domain.schemas import CollectionResult, CollectorQuery, SourceDescriptor
from .base import SourceConnector


class PushOnlyConnectorError(RuntimeError):
    """Raised when a push-only connector is incorrectly used for active collection."""


class InstrumentedAppConnector(SourceConnector):
    """Authorized emulator/app observation ingress contract.

    This connector is push-only. Observations are submitted through the dedicated
    API after an authorized research environment has produced them. It does not
    implement authentication bypasses, CAPTCHA bypasses, anti-bot/device-fingerprint
    evasion, paid-access bypasses, or private-user data collection.
    """

    @property
    def descriptor(self) -> SourceDescriptor:
        return SourceDescriptor(
            source_id="instrumented_app",
            display_name="Instrumented App Observation",
            acquisition_method=AcquisitionMethod.INSTRUMENTED_APP,
            evidence_quality=EvidenceQuality.C,
            acquisition_risk=AcquisitionRisk.R4,
            capabilities={Capability.APP_OBSERVATION, Capability.IMPORT},
            query_mode=QueryMode.PUSH_ONLY,
        )

    def collect(self, query: CollectorQuery) -> CollectionResult:
        raise PushOnlyConnectorError(
            "instrumented_app is push-only; submit authorized observations to "
            "/api/v1/instrumented-app/observations"
        )
