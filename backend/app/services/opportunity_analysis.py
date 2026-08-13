from __future__ import annotations

import json

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

import httpx

from app.core.config import settings
from app.core.http_limits import read_limited_response
from app.domain.citations import (
    CITATION_CONTRACT_VERSION,
    AnalysisCitation,
    evidence_id_for_row,
    validate_analysis_citations,
)
from app.services.provider_registry import EnsembleProvider, FallbackProvider, ProviderCapability, ProviderRegistry, ProviderRouter


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value



@dataclass(frozen=True)
class OpportunityAnalysisInput:
    title: str
    related_keywords: list[str]
    stage: str
    score: float
    risk_score: float
    evidence_types: dict[str, int]
    evidence: list[dict[str, Any]]
    citation_contract_version: str = CITATION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.citation_contract_version != CITATION_CONTRACT_VERSION:
            raise ValueError(
                f"unsupported citation contract version: {self.citation_contract_version}"
            )
        normalized: list[dict[str, Any]] = []
        for row in self.evidence:
            item = dict(row)
            item.setdefault("source", item.get("source_id", ""))
            item.setdefault("type", item.get("evidence_type", ""))
            item.setdefault("quality", item.get("evidence_quality", "E"))
            item.setdefault("url", item.get("source_url"))
            item.setdefault("provenance", "OBSERVED")
            item["evidence_id"] = evidence_id_for_row(item)
            normalized.append(item)
        object.__setattr__(self, "evidence", normalized)


@dataclass(frozen=True)
class OpportunityAnalysisResult:
    summary: str
    target_user: str
    business_model: str
    monetization: str
    risk_notes: str
    provider: str
    citations: list[dict[str, str]] = field(default_factory=list)
    conflict_report: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = []
        for citation in self.citations:
            normalized.append(AnalysisCitation.model_validate(citation).model_dump(mode="json"))
        object.__setattr__(self, "citations", normalized)


class OpportunityAnalyzer(ABC):
    @abstractmethod
    def analyze(self, payload: OpportunityAnalysisInput) -> OpportunityAnalysisResult:
        raise NotImplementedError

    def close(self) -> None:
        return None


class HeuristicOpportunityAnalyzer(OpportunityAnalyzer):
    """Deterministic baseline. It is intentionally not presented as LLM output."""

    def analyze(self, payload: OpportunityAnalysisInput) -> OpportunityAnalysisResult:
        keywords = "、".join(payload.related_keywords[:6]) or payload.title
        kinds = payload.evidence_types
        has_supply = kinds.get("SUPPLY", 0) > 0
        has_execution = kinds.get("EXECUTION", 0) > 0
        has_demand = kinds.get("DEMAND", 0) > 0

        signals = []
        if has_demand:
            signals.append("需求信号")
        if has_supply:
            signals.append("工具/供给信号")
        if has_execution:
            signals.append("招聘/执行信号")
        signal_text = "、".join(signals) or "早期观察信号"
        summary = f"{payload.title} 聚类覆盖 {keywords}；当前出现{signal_text}，阶段为 {payload.stage}。"

        corpus = " ".join(
            f"{row.get('title', '')} {row.get('text', '')}" for row in payload.evidence[:30]
        ).lower()
        if any(term in corpus for term in ("招聘", "运营", "剪辑", "创作者", "creator", "operator")):
            target_user = "内容创作者、运营团队或需要规模化执行该流程的小型团队"
        elif any(term in corpus for term in ("api", "github", "源码", "开发", "developer")):
            target_user = "开发者、自动化工具使用者或技术型团队"
        else:
            target_user = "对该主题存在明确效率或商业需求的个人与小型团队"

        if has_supply and has_execution:
            business_model = "工具/服务供给与实际执行需求同时出现，具备从单点工具向流程化服务扩展的迹象"
        elif has_supply:
            business_model = "以软件、工具、素材、教程或服务形式满足已出现的需求"
        else:
            business_model = "仍以需求发现和内容关注为主，商业供给证据不足"

        if any(term in corpus for term in ("广告", "cps", "分成", "订阅", "saas", "付费", "价格", "出售", "收益", "变现")):
            monetization = "证据中已出现付费、广告、分成、订阅或直接销售等变现线索"
        elif has_supply:
            monetization = "可能通过工具销售、服务费或订阅实现收入，尚需更多真实交易证据验证"
        else:
            monetization = "暂未形成可靠的变现证据"

        if payload.risk_score >= 60:
            risk_notes = "风险信号较强，应优先核验版权、平台规则、授权边界及数据获取合规性"
        elif payload.risk_score > 0:
            risk_notes = "存在部分风险关键词，需要结合具体业务链路核验平台规则、版权和数据使用边界"
        else:
            risk_notes = "当前证据未出现明显高风险关键词，但仍需按具体业务场景做合规核验"

        return OpportunityAnalysisResult(
            summary=summary,
            target_user=target_user,
            business_model=business_model,
            monetization=monetization,
            risk_notes=risk_notes,
            provider="heuristic",
            citations=[
                {
                    "evidence_id": row["evidence_id"],
                    "claim": f"Supporting evidence: {row.get('title') or row.get('text', '')[:400]}".strip(),
                }
                for row in payload.evidence[:30]
            ],
        )


class HttpOpportunityAnalyzer(OpportunityAnalyzer):
    """Vendor-neutral structured analysis adapter.

    The configured endpoint receives the stable Opportunity Radar JSON contract and
    must return JSON with summary/target_user/business_model/monetization/risk_notes.
    It can be backed by an LLM gateway, n8n workflow, or an internal inference service.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 20.0,
        max_response_bytes: int = 1_000_000,
        client: httpx.Client | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.max_response_bytes = max(1_024, int(max_response_bytes))
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=timeout_seconds, follow_redirects=False)

    def analyze(self, payload: OpportunityAnalysisInput) -> OpportunityAnalysisResult:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        with self.client.stream(
            "POST",
            self.endpoint,
            headers=headers,
            json={
                "schema_version": "1",
                "citation_contract_version": payload.citation_contract_version,
                "opportunity": _json_safe(asdict(payload)),
            },
        ) as response:
            response.raise_for_status()
            content = read_limited_response(
                response,
                max_bytes=self.max_response_bytes,
                label="analysis endpoint response",
            )
        body = json.loads(content)
        if not isinstance(body, dict):
            raise ValueError("analysis endpoint returned non-object JSON")
        required = ("summary", "target_user", "business_model", "monetization", "risk_notes")
        missing = [field for field in required if not isinstance(body.get(field), str) or not body[field].strip()]
        if missing:
            raise ValueError(f"analysis endpoint returned invalid structured response; missing={missing}")
        max_field_chars = 20_000
        oversized = [field for field in required if len(body[field]) > max_field_chars]
        if oversized:
            raise ValueError(f"analysis endpoint returned oversized field(s): {oversized}")
        try:
            citations = validate_analysis_citations(
                body.get("citations"),
                allowed_evidence_ids={row["evidence_id"] for row in payload.evidence},
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"analysis endpoint returned invalid structured response; citations={exc}") from exc
        return OpportunityAnalysisResult(
            summary=body["summary"].strip(),
            target_user=body["target_user"].strip(),
            business_model=body["business_model"].strip(),
            monetization=body["monetization"].strip(),
            risk_notes=body["risk_notes"].strip(),
            provider="http",
            citations=citations,
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()


def build_opportunity_analyzer() -> OpportunityAnalyzer:
    return build_analysis_provider_executor()


_analysis_provider_registry: ProviderRegistry | None = None


def build_analysis_provider_registry() -> ProviderRegistry:
    global _analysis_provider_registry
    if _analysis_provider_registry is None:
        registry = ProviderRegistry(circuit_open_seconds=settings.analysis_provider_circuit_open_seconds)
        registry.register(
            "heuristic",
            display_name="Deterministic heuristic analysis",
            capabilities=(ProviderCapability.STRUCTURED_ANALYSIS, ProviderCapability.EVIDENCE_CITATION),
            factory=HeuristicOpportunityAnalyzer,
        )

        def build_http_provider() -> HttpOpportunityAnalyzer:
            if not settings.analysis_http_endpoint:
                raise ValueError("ANALYSIS_HTTP_ENDPOINT is required when ANALYSIS_PROVIDER=http")
            return HttpOpportunityAnalyzer(
                settings.analysis_http_endpoint,
                api_key=settings.analysis_http_api_key,
                timeout_seconds=settings.analysis_http_timeout_seconds,
                max_response_bytes=settings.analysis_http_max_response_bytes,
            )

        registry.register(
            "http",
            display_name="HTTP structured analysis provider",
            capabilities=(ProviderCapability.STRUCTURED_ANALYSIS, ProviderCapability.EVIDENCE_CITATION),
            factory=build_http_provider,
        )
        _analysis_provider_registry = registry
    return _analysis_provider_registry


def build_analysis_provider_router() -> ProviderRouter:
    priority = [item.strip() for item in settings.analysis_provider_priority.split(",") if item.strip()]
    return ProviderRouter(
        build_analysis_provider_registry(),
        priority=priority,
        default_provider_id=settings.analysis_provider,
    )


def build_analysis_provider_executor() -> FallbackProvider:
    registry = build_analysis_provider_registry()
    router = build_analysis_provider_router()
    executor_class = EnsembleProvider if len(router.priority) > 1 else FallbackProvider
    return executor_class(
        registry,
        router,
        capability=ProviderCapability.STRUCTURED_ANALYSIS,
        retry_attempts=settings.analysis_provider_retry_attempts,
        retry_backoff_seconds=settings.analysis_provider_retry_backoff_seconds,
        **({"selection_policy": settings.analysis_provider_selection_policy} if executor_class is EnsembleProvider else {}),
    )
