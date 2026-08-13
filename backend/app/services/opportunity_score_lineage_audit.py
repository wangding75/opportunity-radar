"""Auditable correctness checks for opportunity, score and lineage state."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Keyword,
    NormalizedItem,
    Opportunity,
    OpportunityClusterVersion,
    OpportunityEvidence,
    OpportunityKeyword,
    OpportunityLineage,
    OpportunityScoreSnapshot,
)
from app.services.scoring import SCORING_MODEL_VERSION, ScoreInputs, calculate_score, score_input_signature


OPPORTUNITY_SCORE_LINEAGE_CONTRACT_VERSION = "opportunity-score-lineage-v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SCORE_FIELDS = {
    "demand_score": "demand",
    "supply_score": "supply",
    "execution_score": "execution",
    "cross_source_score": "cross_source",
    "saturation_score": "saturation",
}


def _valid_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _same_number(left: object, right: object, *, places: int = 6) -> bool:
    return _valid_number(left) and _valid_number(right) and round(float(left), places) == round(float(right), places)


def _cluster_signature(keyword_ids: list[int]) -> str:
    return hashlib.sha256(",".join(str(value) for value in sorted(keyword_ids)).encode("utf-8")).hexdigest()


def _violation(violations: list[dict], rule: str, **details: object) -> None:
    violations.append({"rule": rule, **details})


def audit_opportunity_score_lineage(db: Session) -> dict:
    """Audit the persisted Opportunity -> Score -> Lineage business chain.

    The audit deliberately reads persisted rows rather than re-running a refresh.
    That makes drift in historical snapshots, evidence provenance, or lineage
    visible without changing product state. Empty databases are valid and return
    PASS; populated opportunities must satisfy the complete production contract.
    """

    violations: list[dict] = []
    opportunities = db.scalars(select(Opportunity).order_by(Opportunity.id)).all()
    opportunity_ids = {row.id for row in opportunities}
    keywords = db.scalars(select(Keyword).order_by(Keyword.id)).all()
    keyword_ids = {row.id for row in keywords}
    items = {row.id: row for row in db.scalars(select(NormalizedItem)).all()}

    keyword_links = db.scalars(select(OpportunityKeyword).order_by(OpportunityKeyword.id)).all()
    links_by_opportunity: dict[int, list[OpportunityKeyword]] = defaultdict(list)
    link_keys: list[tuple[int, int]] = []
    for row in keyword_links:
        link_keys.append((row.opportunity_id, row.keyword_id))
        if row.opportunity_id not in opportunity_ids:
            _violation(violations, "opportunity_keyword_references_opportunity", link_id=row.id)
        if row.keyword_id not in keyword_ids:
            _violation(violations, "opportunity_keyword_references_keyword", link_id=row.id)
        if not row.role or not row.role.strip():
            _violation(violations, "opportunity_keyword_role_present", link_id=row.id)
        if not _valid_number(row.weight) or float(row.weight) < 0:
            _violation(violations, "opportunity_keyword_weight_valid", link_id=row.id)
        links_by_opportunity[row.opportunity_id].append(row)
    for key, count in Counter(link_keys).items():
        if count > 1:
            _violation(violations, "opportunity_keyword_idempotency", key=list(key), count=count)

    evidence_rows = db.scalars(select(OpportunityEvidence).order_by(OpportunityEvidence.id)).all()
    evidence_by_opportunity: Counter[int] = Counter()
    evidence_keys: list[tuple[int, int]] = []
    for row in evidence_rows:
        evidence_keys.append((row.opportunity_id, row.normalized_item_id))
        if row.opportunity_id not in opportunity_ids:
            _violation(violations, "opportunity_evidence_references_opportunity", evidence_id=row.id)
        item = items.get(row.normalized_item_id)
        if item is None:
            _violation(violations, "opportunity_evidence_references_normalized_item", evidence_id=row.id)
        elif row.observed_at != item.observed_at:
            _violation(violations, "opportunity_evidence_mirrors_observed_at", evidence_id=row.id)
        if not row.evidence_type or not row.evidence_type.strip():
            _violation(violations, "opportunity_evidence_type_present", evidence_id=row.id)
        if not _valid_number(row.weight) or float(row.weight) < 0:
            _violation(violations, "opportunity_evidence_weight_valid", evidence_id=row.id)
        evidence_by_opportunity[row.opportunity_id] += 1
    for key, count in Counter(evidence_keys).items():
        if count > 1:
            _violation(violations, "opportunity_evidence_idempotency", key=list(key), count=count)

    snapshots = db.scalars(select(OpportunityScoreSnapshot).order_by(OpportunityScoreSnapshot.id)).all()
    snapshot_keys: list[tuple[int, str, str]] = []
    snapshots_by_opportunity: Counter[int] = Counter()
    opportunity_by_id = {row.id: row for row in opportunities}
    for row in snapshots:
        snapshot_keys.append((row.opportunity_id, row.model_version, row.input_signature))
        opportunity = opportunity_by_id.get(row.opportunity_id)
        if opportunity is None:
            _violation(violations, "score_snapshot_references_opportunity", snapshot_id=row.id)
        else:
            snapshots_by_opportunity[row.opportunity_id] += 1
        if not row.model_version or len(row.model_version) > 40:
            _violation(violations, "score_snapshot_model_version_present", snapshot_id=row.id)
        if isinstance(row.breakdown, dict) and row.breakdown.get("model_version") not in {None, row.model_version}:
            _violation(violations, "score_snapshot_breakdown_model_matches_snapshot", snapshot_id=row.id)
        if not _SHA256.fullmatch(row.input_signature or ""):
            _violation(violations, "score_snapshot_signature_format", snapshot_id=row.id)
        expected_signature = score_input_signature(
            row.breakdown or {},
            risk_score=row.risk_score,
            stage=row.stage,
            evidence_count=row.evidence_count,
        )
        if row.input_signature != expected_signature:
            _violation(violations, "score_snapshot_signature_matches_payload", snapshot_id=row.id)
        if not _valid_number(row.score) or not 0 <= float(row.score) <= 100:
            _violation(violations, "score_snapshot_score_range", snapshot_id=row.id)
        if not _valid_number(row.risk_score) or not 0 <= float(row.risk_score) <= 100:
            _violation(violations, "score_snapshot_risk_range", snapshot_id=row.id)
        if row.evidence_count < 0:
            _violation(violations, "score_snapshot_evidence_count_range", snapshot_id=row.id)
        if row.calculated_at is None:
            _violation(violations, "score_snapshot_timestamp_present", snapshot_id=row.id)
    for key, count in Counter(snapshot_keys).items():
        if count > 1:
            _violation(violations, "score_snapshot_idempotency", key=list(key), count=count)

    cluster_versions = db.scalars(select(OpportunityClusterVersion).order_by(OpportunityClusterVersion.opportunity_id, OpportunityClusterVersion.generation)).all()
    versions_by_opportunity: dict[int, list[OpportunityClusterVersion]] = defaultdict(list)
    for row in cluster_versions:
        versions_by_opportunity[row.opportunity_id].append(row)
        if row.opportunity_id not in opportunity_ids:
            _violation(violations, "cluster_version_references_opportunity", cluster_version_id=row.id)
        keyword_list = row.keyword_ids if isinstance(row.keyword_ids, list) else []
        if row.generation < 1:
            _violation(violations, "cluster_generation_positive", cluster_version_id=row.id)
        if not keyword_list:
            _violation(violations, "cluster_keyword_ids_present", cluster_version_id=row.id)
        if not _SHA256.fullmatch(row.cluster_signature or ""):
            _violation(violations, "cluster_signature_format", cluster_version_id=row.id)
        keyword_ids_are_ints = all(isinstance(value, int) and not isinstance(value, bool) for value in keyword_list)
        if not keyword_ids_are_ints or keyword_list != sorted(set(keyword_list)):
            _violation(violations, "cluster_keyword_ids_canonical", cluster_version_id=row.id)
        if keyword_ids_are_ints and _cluster_signature(keyword_list) != row.cluster_signature:
            _violation(violations, "cluster_signature_matches_keywords", cluster_version_id=row.id)
        if any(value not in keyword_ids for value in keyword_list):
            _violation(violations, "cluster_keywords_reference_existing_keywords", cluster_version_id=row.id)
        if row.started_at is None or (row.ended_at is not None and row.ended_at < row.started_at):
            _violation(violations, "cluster_version_time_order", cluster_version_id=row.id)

    lineage_rows = db.scalars(select(OpportunityLineage).order_by(OpportunityLineage.id)).all()
    lineage_keys: list[tuple[int, int, str]] = []
    adjacency: dict[int, set[int]] = defaultdict(set)
    for row in lineage_rows:
        key = (row.parent_opportunity_id, row.child_opportunity_id, row.relation_type)
        lineage_keys.append(key)
        if row.parent_opportunity_id not in opportunity_ids or row.child_opportunity_id not in opportunity_ids:
            _violation(violations, "lineage_references_existing_opportunities", lineage_id=row.id)
        if row.parent_opportunity_id == row.child_opportunity_id:
            _violation(violations, "lineage_no_self_edge", lineage_id=row.id)
        if not row.relation_type or not row.relation_type.strip():
            _violation(violations, "lineage_relation_type_present", lineage_id=row.id)
        if row.created_at is None:
            _violation(violations, "lineage_timestamp_present", lineage_id=row.id)
        if row.parent_opportunity_id in opportunity_ids and row.child_opportunity_id in opportunity_ids:
            adjacency[row.parent_opportunity_id].add(row.child_opportunity_id)
    for key, count in Counter(lineage_keys).items():
        if count > 1:
            _violation(violations, "lineage_idempotency", key=list(key), count=count)

    state: dict[int, int] = {}
    stack: list[int] = []
    stack_index: dict[int, int] = {}
    seen_cycles: set[tuple[int, ...]] = set()

    def visit(node: int) -> None:
        state[node] = 1
        stack_index[node] = len(stack)
        stack.append(node)
        for child in sorted(adjacency.get(node, set())):
            if state.get(child, 0) == 0:
                visit(child)
            elif state.get(child) == 1:
                cycle = tuple(stack[stack_index[child]:] + [child])
                if cycle not in seen_cycles:
                    seen_cycles.add(cycle)
                    _violation(violations, "lineage_is_acyclic", cycle=list(cycle))
        stack.pop()
        stack_index.pop(node, None)
        state[node] = 2

    for opportunity_id in sorted(opportunity_ids):
        if state.get(opportunity_id, 0) == 0:
            visit(opportunity_id)

    for opportunity in opportunities:
        if not opportunity.opportunity_key or not opportunity.opportunity_key.strip():
            _violation(violations, "opportunity_key_present", opportunity_id=opportunity.id)
        if opportunity.keyword_id not in keyword_ids:
            _violation(violations, "opportunity_primary_keyword_exists", opportunity_id=opportunity.id)
        if not _valid_number(opportunity.score) or not 0 <= float(opportunity.score) <= 100:
            _violation(violations, "opportunity_score_range", opportunity_id=opportunity.id)
        if not _valid_number(opportunity.risk_score) or not 0 <= float(opportunity.risk_score) <= 100:
            _violation(violations, "opportunity_risk_range", opportunity_id=opportunity.id)
        if opportunity.evidence_count < 0 or opportunity.evidence_count != evidence_by_opportunity[opportunity.id]:
            _violation(violations, "opportunity_evidence_count_matches_rows", opportunity_id=opportunity.id)

        links = links_by_opportunity[opportunity.id]
        primary_links = [row for row in links if row.role == "PRIMARY"]
        if not links:
            _violation(violations, "opportunity_has_keyword_links", opportunity_id=opportunity.id)
        if len(primary_links) != 1 or primary_links[0].keyword_id != opportunity.keyword_id:
            _violation(violations, "opportunity_primary_keyword_link", opportunity_id=opportunity.id)
        if opportunity.related_keyword_count != len(links):
            _violation(violations, "opportunity_related_keyword_count", opportunity_id=opportunity.id)

        breakdown = opportunity.score_breakdown if isinstance(opportunity.score_breakdown, dict) else {}
        if not breakdown:
            _violation(violations, "opportunity_score_breakdown_present", opportunity_id=opportunity.id)
        if not opportunity.score_version:
            _violation(violations, "opportunity_score_version_present", opportunity_id=opportunity.id)
        if breakdown.get("model_version") != opportunity.score_version:
            _violation(violations, "opportunity_score_model_matches_version", opportunity_id=opportunity.id)
        total = breakdown.get("total")
        if not _valid_number(total) or not 0 <= float(total) <= 100:
            _violation(violations, "opportunity_breakdown_total_range", opportunity_id=opportunity.id)
        elif not _same_number(opportunity.score, total):
            _violation(violations, "opportunity_score_matches_breakdown", opportunity_id=opportunity.id)

        components = breakdown.get("components")
        component_names = ("demand", "supply", "execution", "cross_source", "saturation")
        if not isinstance(components, dict) or any(not _valid_number(components.get(name)) for name in component_names):
            _violation(violations, "opportunity_breakdown_components_present", opportunity_id=opportunity.id)
        else:
            for field, component_name in _SCORE_FIELDS.items():
                if not _same_number(getattr(opportunity, field), components[component_name], places=2):
                    _violation(violations, "opportunity_score_component_matches_breakdown", opportunity_id=opportunity.id, field=field)

        inputs = breakdown.get("inputs")
        # Dormant snapshots intentionally contain a reason and zero components,
        # with no scoring inputs because no active evidence was available.
        if opportunity.stage != "DORMANT":
            if not isinstance(inputs, dict):
                _violation(violations, "active_opportunity_score_inputs_present", opportunity_id=opportunity.id)
            else:
                try:
                    expected_score, expected_breakdown = calculate_score(ScoreInputs(**inputs))
                except (TypeError, ValueError):
                    _violation(violations, "active_opportunity_score_inputs_valid", opportunity_id=opportunity.id)
                else:
                    if opportunity.score_version == SCORING_MODEL_VERSION:
                        if not _same_number(expected_score, opportunity.score, places=2):
                            _violation(violations, "active_opportunity_score_recomputes", opportunity_id=opportunity.id)
                        if expected_breakdown["components"] != components:
                            _violation(violations, "active_opportunity_components_recompute", opportunity_id=opportunity.id)

        if snapshots_by_opportunity[opportunity.id] == 0:
            _violation(violations, "opportunity_has_score_snapshot", opportunity_id=opportunity.id)

        versions = versions_by_opportunity[opportunity.id]
        if not versions:
            if opportunity.cluster_generation != 0 or opportunity.cluster_signature:
                _violation(violations, "opportunity_cluster_state_has_version", opportunity_id=opportunity.id)
        else:
            generations = [row.generation for row in versions]
            if generations != list(range(1, len(generations) + 1)):
                _violation(violations, "cluster_generations_contiguous", opportunity_id=opportunity.id)
            open_versions = [row for row in versions if row.ended_at is None]
            if len(open_versions) > 1:
                _violation(violations, "cluster_one_open_version", opportunity_id=opportunity.id)
            latest = versions[-1]
            if opportunity.cluster_generation != latest.generation or opportunity.cluster_signature != latest.cluster_signature:
                _violation(violations, "opportunity_cluster_state_matches_latest_version", opportunity_id=opportunity.id)

    return {
        "audit_id": "opportunity-radar-opportunity-score-lineage",
        "contract_version": OPPORTUNITY_SCORE_LINEAGE_CONTRACT_VERSION,
        "status": "PASS" if not violations else "FAIL",
        "violations": violations,
        "summary": {
            "opportunities": len(opportunities),
            "keywords": len(keywords),
            "keyword_links": len(keyword_links),
            "evidence_rows": len(evidence_rows),
            "score_snapshots": len(snapshots),
            "cluster_versions": len(cluster_versions),
            "lineage_edges": len(lineage_rows),
            "lineage_cycles": sum(1 for row in violations if row["rule"] == "lineage_is_acyclic"),
            "real_data_collected": 0,
            "data_policy": "SYNTHETIC_OR_MOCK_ONLY",
        },
    }
