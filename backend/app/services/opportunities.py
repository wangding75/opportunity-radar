from __future__ import annotations

import hashlib
import json
import uuid
from collections import Counter, defaultdict, deque
from datetime import timedelta

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
from app.domain.citations import (
    CITATION_CONTRACT_VERSION,
    evidence_id_for_content_hash,
    evidence_id_for_row,
    provenance_from_payload,
)
from app.db.models import (
    Keyword,
    KeywordMention,
    KeywordRelation,
    NormalizedItem,
    Opportunity,
    OpportunityClusterVersion,
    OpportunityEvidence,
    OpportunityKeyword,
    OpportunityLineage,
    OpportunityResearch,
    RawObservation,
)
from app.domain.enums import ItemType, KeywordStatus
from app.services.graph import connected_keyword_ids
from app.services.opportunity_analysis import HeuristicOpportunityAnalyzer, OpportunityAnalysisInput
from app.services.scoring import SCORING_MODEL_VERSION, ScoreInputs, calculate_score, record_score_snapshot
from app.services.citations import bind_citation_selection, select_evidence_citations

RISK_TERMS = {"侵权", "封号", "违规", "投诉", "版权", "破解", "绕过", "盗版", "灰产", "黑产", "ban", "copyright", "piracy"}
COMMERCIAL_TERMS = {"工具", "软件", "系统", "源码", "教程", "素材", "价格", "出售", "收益", "变现", "tool", "software", "saas", "course"}
QUALITY_WEIGHT = {"A": 1.0, "B": 0.9, "C": 0.75, "D": 0.5, "E": 0.25}
CLUSTER_RELATION_MIN_WEIGHT = 12.0
MAX_ANALYSIS_KEYWORDS = 12


def _evidence_type(item: NormalizedItem) -> str:
    if item.item_type == ItemType.JOB.value:
        return "EXECUTION"
    if item.item_type in {ItemType.PRODUCT.value, ItemType.REPOSITORY.value}:
        return "SUPPLY"
    if item.item_type == ItemType.TREND.value:
        return "DEMAND"
    text = f"{item.title} {item.text}".lower()
    if any(term in text for term in COMMERCIAL_TERMS):
        return "SUPPLY"
    return "DEMAND"


def _business_risk(items: list[NormalizedItem]) -> float:
    hits = 0
    for item in items:
        text = f"{item.title} {item.text}".lower()
        hits += sum(1 for term in RISK_TERMS if term in text)
    return round(min(100.0, hits * 15.0), 2)


def _stage(types: Counter[str], primary: Keyword) -> str:
    if types["EXECUTION"] > 0 and types["SUPPLY"] > 0:
        return "COMMERCIALIZING"
    if types["SUPPLY"] > 0:
        return "PRODUCTIZING"
    if primary.status == KeywordStatus.TRENDING.value:
        return "EARLY_GROWTH"
    return "DISCOVERY"


def _candidate_keywords(db: Session, cutoff, *, ids: set[int] | None = None, limit: int | None = None) -> list[Keyword]:
    stmt = select(Keyword).where(
        Keyword.last_seen_at >= cutoff,
        (Keyword.source_count >= 2) | (Keyword.observation_count >= 3),
    )
    if ids is not None:
        if not ids:
            return []
        stmt = stmt.where(Keyword.id.in_(ids))
    stmt = stmt.order_by(Keyword.score.desc(), Keyword.last_seen_at.desc())
    if limit is not None:
        stmt = stmt.limit(limit)
    return db.scalars(stmt).all()


def _cluster_keywords(db: Session, keywords: list[Keyword], cutoff) -> list[list[Keyword]]:
    if not keywords:
        return []
    by_id = {kw.id: kw for kw in keywords}
    candidate_ids = set(by_id)
    adjacency: dict[int, set[int]] = defaultdict(set)
    relations = db.scalars(
        select(KeywordRelation).where(
            KeywordRelation.keyword_a_id.in_(candidate_ids),
            KeywordRelation.keyword_b_id.in_(candidate_ids),
            KeywordRelation.last_seen_at >= cutoff,
            KeywordRelation.weight >= CLUSTER_RELATION_MIN_WEIGHT,
        )
    ).all()
    for rel in relations:
        adjacency[rel.keyword_a_id].add(rel.keyword_b_id)
        adjacency[rel.keyword_b_id].add(rel.keyword_a_id)

    seen: set[int] = set()
    components: list[list[Keyword]] = []
    for keyword in keywords:
        if keyword.id in seen:
            continue
        queue = deque([keyword.id])
        component_ids: list[int] = []
        seen.add(keyword.id)
        while queue:
            current = queue.popleft()
            component_ids.append(current)
            for neighbor in adjacency.get(current, set()):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        component = [by_id[key] for key in component_ids]
        component.sort(key=lambda kw: (kw.score, kw.source_count, kw.observation_count, -kw.id), reverse=True)
        # Keep the complete strong-connected component. Truncating here silently
        # dropped cluster members, their evidence, and their opportunity identity.
        # Only the external-analysis payload is bounded later.
        components.append(component)
    return components


def _analysis_signature(payload: OpportunityAnalysisInput) -> str:
    stable = {
        "title": payload.title,
        "related_keywords": payload.related_keywords,
        "stage": payload.stage,
        "score": payload.score,
        "risk_score": payload.risk_score,
        "evidence_types": payload.evidence_types,
        "evidence": [
            {
                "source": row.get("source"),
                "type": row.get("type"),
                "item_type": row.get("item_type"),
                "quality": row.get("quality"),
                "title": row.get("title"),
                "text_hash": hashlib.sha256(str(row.get("text", "")).encode("utf-8")).hexdigest(),
                "url": row.get("url"),
                "observed_at": str(row.get("observed_at")),
            }
            for row in payload.evidence[:30]
        ],
    }
    return hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _cluster_signature(keyword_ids: set[int]) -> str:
    return hashlib.sha256(",".join(str(v) for v in sorted(keyword_ids)).encode()).hexdigest()


def _external_analysis_enabled() -> bool:
    if settings.analysis_provider == "heuristic":
        return False
    if settings.analysis_provider == "http":
        return True
    raise ValueError(f"unsupported ANALYSIS_PROVIDER: {settings.analysis_provider}")


def _bounded(value: str | None, limit: int) -> str:
    if not value:
        return ""
    return value[: max(0, limit)]


def _representative_analysis_evidence(items: list[NormalizedItem], raw_by_id: dict[int, RawObservation], *, limit: int) -> list[dict]:
    ordered = sorted(items, key=lambda row: row.observed_at, reverse=True)
    rows: list[dict] = []
    for item in ordered:
        raw = raw_by_id.get(item.raw_observation_id)
        rows.append({
            "evidence_id": evidence_id_for_content_hash(raw.content_hash) if raw else evidence_id_for_row({
                "source": item.source_id,
                "type": _evidence_type(item),
                "item_type": item.item_type,
                "title": item.title,
                "text": item.text,
                "url": item.source_url,
                "observed_at": item.observed_at,
            }),
            "source": item.source_id,
            "type": _evidence_type(item),
            "item_type": item.item_type,
            "quality": raw.evidence_quality if raw else "E",
            "acquisition_method": raw.acquisition_method if raw else "UNKNOWN",
            "provenance": provenance_from_payload(raw.raw_payload if raw else None),
            "title": _bounded(item.title, 500),
            "text": _bounded(item.text, max(0, settings.analysis_evidence_text_chars)),
            "url": _bounded(item.source_url, 2_000),
            "observed_at": item.observed_at,
        })
    return select_evidence_citations(rows, limit=limit)


def _apply_analysis_result(opportunity: Opportunity, result, *, now) -> None:
    opportunity.summary = result.summary
    opportunity.target_user = result.target_user
    opportunity.business_model = result.business_model
    opportunity.monetization = result.monetization
    opportunity.risk_notes = result.risk_notes
    opportunity.analysis_provider = result.provider
    opportunity.analysis_citations = list(result.citations)
    opportunity.analysis_conflict = dict(result.conflict_report or {})
    opportunity.analyzed_at = now


def _opportunity_keyword_sets(db: Session, opportunity_ids: set[int]) -> dict[int, set[int]]:
    if not opportunity_ids:
        return {}
    result: dict[int, set[int]] = defaultdict(set)
    rows = db.execute(
        select(OpportunityKeyword.opportunity_id, OpportunityKeyword.keyword_id).where(
            OpportunityKeyword.opportunity_id.in_(opportunity_ids)
        )
    ).all()
    for opportunity_id, keyword_id in rows:
        result[opportunity_id].add(keyword_id)
    return dict(result)


def _record_lineage(db: Session, parent_id: int, child_id: int, relation_type: str, *, now) -> None:
    if parent_id == child_id:
        return
    # SessionLocal deliberately uses autoflush=False. Check both persisted rows and
    # pending ORM objects so repeated lineage generation inside one transaction
    # cannot enqueue duplicate rows and then fail the unique constraint at commit.
    for pending in db.new:
        if (
            isinstance(pending, OpportunityLineage)
            and pending.parent_opportunity_id == parent_id
            and pending.child_opportunity_id == child_id
            and pending.relation_type == relation_type
        ):
            return
    existing = db.scalar(select(OpportunityLineage.id).where(
        OpportunityLineage.parent_opportunity_id == parent_id,
        OpportunityLineage.child_opportunity_id == child_id,
        OpportunityLineage.relation_type == relation_type,
    ))
    if existing is None:
        db.add(OpportunityLineage(
            parent_opportunity_id=parent_id,
            child_opportunity_id=child_id,
            relation_type=relation_type,
            created_at=now,
        ))


def _record_cluster_version(db: Session, opportunity: Opportunity, keyword_ids: set[int], *, change_type: str, now) -> bool:
    signature = _cluster_signature(keyword_ids)
    if opportunity.cluster_signature == signature:
        return False
    active = db.scalar(
        select(OpportunityClusterVersion)
        .where(OpportunityClusterVersion.opportunity_id == opportunity.id, OpportunityClusterVersion.ended_at.is_(None))
        .order_by(OpportunityClusterVersion.generation.desc())
        .limit(1)
    )
    if active is not None:
        active.ended_at = now
    opportunity.cluster_generation = int(opportunity.cluster_generation or 0) + 1
    opportunity.cluster_signature = signature
    db.add(OpportunityClusterVersion(
        opportunity_id=opportunity.id,
        generation=opportunity.cluster_generation,
        cluster_signature=signature,
        keyword_ids=sorted(keyword_ids),
        change_type=change_type,
        started_at=now,
    ))
    return True


def _new_opportunity(db: Session, primary: Keyword) -> Opportunity:
    row = Opportunity(
        opportunity_key=f"opp:{uuid.uuid4().hex}",
        keyword_id=primary.id,
        title=primary.display_name,
        stage="DISCOVERY",
    )
    db.add(row)
    db.flush()
    return row


def _select_impacted_scope(db: Session, affected_keyword_ids: set[int]) -> set[int]:
    if not affected_keyword_ids:
        return set()
    linked = set(db.scalars(
        select(OpportunityKeyword.keyword_id).where(
            OpportunityKeyword.opportunity_id.in_(
                select(OpportunityKeyword.opportunity_id).where(OpportunityKeyword.keyword_id.in_(affected_keyword_ids))
            )
        )
    ).all())
    return connected_keyword_ids(
        db,
        set(affected_keyword_ids) | linked,
        since_days=90,
        min_weight=CLUSTER_RELATION_MIN_WEIGHT,
    )


def _match_components(
    db: Session,
    components: list[list[Keyword]],
    existing_opportunities: list[Opportunity],
    existing_sets: dict[int, set[int]],
    *,
    now,
) -> list[tuple[list[Keyword], Opportunity, str]]:
    """Match new graph components to stable opportunities deterministically.

    A historic opportunity that splits across multiple components must keep its
    identity on the component with the strongest overlap, independent of component
    iteration order. Secondary fragments become children and are linked through
    lineage records. Multiple historic opportunities that prefer the same new
    component are treated as a merge.
    """
    research_rows = db.scalars(
        select(OpportunityResearch).where(OpportunityResearch.opportunity_id.in_([o.id for o in existing_opportunities]))
    ).all() if existing_opportunities else []
    research = {r.opportunity_id: r for r in research_rows}

    component_sets = [{kw.id for kw in component} for component in components]
    overlap_by_component: dict[int, list[tuple[float, int, int, int, Opportunity]]] = defaultdict(list)
    preferred_component_by_opp: dict[int, int] = {}

    for opp in existing_opportunities:
        old = existing_sets.get(opp.id, set())
        if not old:
            continue
        state = research.get(opp.id)
        research_bonus = 1 if state and (state.starred or state.status != "NEW" or state.priority > 0) else 0
        choices: list[tuple[float, int, float, int, int]] = []
        for index, ids in enumerate(component_sets):
            inter = len(ids & old)
            if not inter:
                continue
            union = len(ids | old) or 1
            jaccard = inter / union
            component_score = sum(float(kw.score or 0.0) for kw in components[index])
            overlap_by_component[index].append((jaccard, inter, research_bonus, -opp.id, opp))
            # Identity follows overlap first; component score and deterministic index
            # are only tie-breakers. This avoids assigning the historic identity to
            # whichever split fragment happens to be iterated first.
            choices.append((jaccard, inter, component_score, -index, index))
        if choices:
            choices.sort(reverse=True)
            preferred_component_by_opp[opp.id] = choices[0][4]

    assigned: list[tuple[list[Keyword], Opportunity, str]] = []
    used: set[int] = set()
    for index, component in enumerate(components):
        overlaps = overlap_by_component.get(index, [])
        overlaps.sort(reverse=True, key=lambda row: row[:4])
        owners = [row for row in overlaps if preferred_component_by_opp.get(row[4].id) == index and row[4].id not in used]

        if owners:
            opportunity = owners[0][4]
            used.add(opportunity.id)
            merge_parents = [row[4] for row in owners[1:]]
            for parent in merge_parents:
                used.add(parent.id)
                _record_lineage(db, parent.id, opportunity.id, "MERGED_INTO", now=now)
                parent.stage = "DORMANT"
                parent.updated_at = now

            secondary_parents = [
                row[4] for row in overlaps
                if row[4].id != opportunity.id and preferred_component_by_opp.get(row[4].id) != index
            ]
            for parent in secondary_parents:
                _record_lineage(db, parent.id, opportunity.id, "SPLIT_MERGED_INTO", now=now)

            change_type = "MERGED" if merge_parents else ("SPLIT_MERGED" if secondary_parents else "UPDATED")
        elif overlaps:
            # This is a secondary fragment of one or more historic opportunities;
            # create a new stable child instead of stealing a parent's identity.
            opportunity = _new_opportunity(db, component[0])
            parents = [row[4] for row in overlaps]
            relation_type = "SPLIT_INTO" if len(parents) == 1 else "SPLIT_MERGED_INTO"
            for parent in parents:
                _record_lineage(db, parent.id, opportunity.id, relation_type, now=now)
            change_type = "SPLIT" if len(parents) == 1 else "SPLIT_MERGED"
        else:
            opportunity = _new_opportunity(db, component[0])
            change_type = "CREATED"

        assigned.append((component, opportunity, change_type))
    return assigned


def refresh_opportunities(
    db: Session,
    *,
    limit: int | None = None,
    affected_keyword_ids: set[int] | None = None,
    progress_callback=None,
) -> set[int]:
    """Refresh opportunities globally or only around changed keyword components.

    Opportunity identity is stable: cluster changes are matched by keyword overlap;
    the historic opportunity_key is never rewritten after 0.7. Merge/split lineage
    and cluster versions preserve research continuity and auditability.
    """
    now = utc_now()
    cutoff = now - timedelta(days=90)
    external_analysis = _external_analysis_enabled()

    if affected_keyword_ids is None:
        if limit is None:
            keywords = _candidate_keywords(db, cutoff)
            existing_opportunities = db.scalars(select(Opportunity)).all()
        else:
            # `limit` bounds the number of seed candidates, not the membership of
            # their strong-connected clusters. Truncating the keyword list itself
            # would silently shrink a real cluster and overwrite its stable identity.
            seed_keywords = _candidate_keywords(db, cutoff, limit=limit)
            seed_ids = {kw.id for kw in seed_keywords}
            scope_ids = connected_keyword_ids(
                db,
                seed_ids,
                since_days=90,
                min_weight=CLUSTER_RELATION_MIN_WEIGHT,
            )
            keywords = _candidate_keywords(db, cutoff, ids=scope_ids)
            existing_ids = set(db.scalars(
                select(OpportunityKeyword.opportunity_id).where(
                    OpportunityKeyword.keyword_id.in_(scope_ids)
                )
            ).all()) if scope_ids else set()
            existing_opportunities = db.scalars(
                select(Opportunity).where(Opportunity.id.in_(existing_ids))
            ).all() if existing_ids else []
    else:
        scope_ids = _select_impacted_scope(db, set(affected_keyword_ids))
        keywords = _candidate_keywords(db, cutoff, ids=scope_ids)
        existing_ids = set(db.scalars(
            select(OpportunityKeyword.opportunity_id).where(OpportunityKeyword.keyword_id.in_(scope_ids or affected_keyword_ids))
        ).all())
        existing_opportunities = db.scalars(select(Opportunity).where(Opportunity.id.in_(existing_ids))).all() if existing_ids else []

    existing_sets = _opportunity_keyword_sets(db, {o.id for o in existing_opportunities})
    components = _cluster_keywords(db, keywords, cutoff)
    assigned = _match_components(db, components, existing_opportunities, existing_sets, now=now)
    processed_ids: set[int] = set()
    heuristic = HeuristicOpportunityAnalyzer()

    for component_index, (component, opportunity, change_type) in enumerate(assigned, start=1):
        primary = component[0]
        keyword_ids = {kw.id for kw in component}
        historical_first_seen = db.scalar(
            select(func.min(KeywordMention.observed_at)).where(KeywordMention.keyword_id.in_(keyword_ids))
        )
        recent_item_ids = list(dict.fromkeys(db.scalars(
            select(KeywordMention.normalized_item_id)
            .where(KeywordMention.keyword_id.in_(keyword_ids), KeywordMention.observed_at >= cutoff)
            .order_by(KeywordMention.observed_at.desc())
        ).all()))
        if not recent_item_ids:
            continue
        recent_items = db.scalars(select(NormalizedItem).where(NormalizedItem.id.in_(recent_item_ids))).all()
        if not recent_items:
            continue
        raw_ids = [item.raw_observation_id for item in recent_items]
        raw_rows = db.scalars(select(RawObservation).where(RawObservation.id.in_(raw_ids))).all()
        raw_by_id = {row.id: row for row in raw_rows}

        evidence_types = Counter(_evidence_type(item) for item in recent_items)
        weighted_types: Counter[str] = Counter()
        for item in recent_items:
            raw = raw_by_id.get(item.raw_observation_id)
            weighted_types[_evidence_type(item)] += QUALITY_WEIGHT.get(raw.evidence_quality if raw else "E", 0.25)
        recent_sources = {item.source_id for item in recent_items}
        recent_30 = [item for item in recent_items if item.observed_at >= now - timedelta(days=30)]
        trend_items = [item for item in recent_items if item.item_type == ItemType.TREND.value]
        trend_last_7 = sum(1 for item in trend_items if item.observed_at >= now - timedelta(days=7))
        trend_prev_7 = sum(1 for item in trend_items if now - timedelta(days=14) <= item.observed_at < now - timedelta(days=7))
        score, score_breakdown = calculate_score(ScoreInputs(
            weighted_demand=float(weighted_types["DEMAND"]),
            weighted_supply=float(weighted_types["SUPPLY"]),
            weighted_execution=float(weighted_types["EXECUTION"]),
            source_count=len(recent_sources),
            recent_30_count=len(recent_30),
            trend_last_7=trend_last_7,
            trend_prev_7=trend_prev_7,
        ))
        score_components = score_breakdown["components"]
        demand_score = score_components["demand"]
        supply_score = score_components["supply"]
        execution_score = score_components["execution"]
        cross_source_score = score_components["cross_source"]
        saturation_score = score_components["saturation"]
        risk_score = _business_risk(recent_items)
        stage = _stage(evidence_types, primary)

        opportunity.keyword_id = primary.id
        opportunity.title = primary.display_name
        opportunity.stage = stage
        opportunity.score = score
        opportunity.demand_score = round(demand_score, 2)
        opportunity.supply_score = round(supply_score, 2)
        opportunity.execution_score = round(execution_score, 2)
        opportunity.cross_source_score = round(cross_source_score, 2)
        opportunity.saturation_score = round(saturation_score, 2)
        opportunity.risk_score = risk_score
        opportunity.score_version = SCORING_MODEL_VERSION
        opportunity.score_breakdown = score_breakdown
        opportunity.evidence_count = len(recent_items)
        opportunity.first_seen_at = historical_first_seen or min(item.observed_at for item in recent_items)
        opportunity.last_seen_at = max(item.observed_at for item in recent_items)
        opportunity.updated_at = now
        opportunity.related_keyword_count = len(component)
        _record_cluster_version(db, opportunity, keyword_ids, change_type=change_type, now=now)

        db.execute(delete(OpportunityKeyword).where(OpportunityKeyword.opportunity_id == opportunity.id))
        for index, keyword in enumerate(component):
            db.add(OpportunityKeyword(
                opportunity_id=opportunity.id,
                keyword_id=keyword.id,
                role="PRIMARY" if index == 0 else "RELATED",
                weight=keyword.score,
            ))
        db.execute(delete(OpportunityEvidence).where(OpportunityEvidence.opportunity_id == opportunity.id))
        for item in sorted(recent_items, key=lambda row: row.observed_at, reverse=True)[:100]:
            raw = raw_by_id.get(item.raw_observation_id)
            db.add(OpportunityEvidence(
                opportunity_id=opportunity.id,
                normalized_item_id=item.id,
                evidence_type=_evidence_type(item),
                weight=QUALITY_WEIGHT.get(raw.evidence_quality if raw else "E", 0.25),
                observed_at=item.observed_at,
            ))

        analysis_input = OpportunityAnalysisInput(
            title=opportunity.title,
            related_keywords=[kw.display_name for kw in component[:MAX_ANALYSIS_KEYWORDS]],
            stage=stage,
            score=score,
            risk_score=risk_score,
            evidence_types=dict(evidence_types),
            evidence=_representative_analysis_evidence(recent_items, raw_by_id, limit=max(1, min(100, settings.analysis_evidence_limit))),
        )
        signature = _analysis_signature(analysis_input)
        if opportunity.analysis_signature != signature:
            result = heuristic.analyze(analysis_input)
            _apply_analysis_result(opportunity, result, now=now)
            opportunity.analysis_signature = signature
            opportunity.analysis_attempt_count = 0
            opportunity.analysis_last_attempt_at = None
            opportunity.analysis_error = None
            if external_analysis:
                opportunity.analysis_status = "PENDING"
                opportunity.analysis_provider = "heuristic_pending"
                opportunity.analysis_next_retry_at = now
            else:
                opportunity.analysis_status = "READY"
                opportunity.analysis_provider = "heuristic"
                opportunity.analysis_next_retry_at = None
        elif not external_analysis and opportunity.analysis_provider != "heuristic":
            result = heuristic.analyze(analysis_input)
            _apply_analysis_result(opportunity, result, now=now)
            opportunity.analysis_status = "READY"
            opportunity.analysis_provider = "heuristic"
            opportunity.analysis_error = None
            opportunity.analysis_next_retry_at = None
        processed_ids.add(opportunity.id)
        record_score_snapshot(db, opportunity, now=now)
        if progress_callback is not None and component_index % 25 == 0:
            progress_callback()

    assigned_ids = {opp.id for _component, opp, _change in assigned}
    for old in existing_opportunities:
        if old.id not in assigned_ids:
            old.stage = "DORMANT"
            old.score = 0.0
            old.demand_score = 0.0
            old.supply_score = 0.0
            old.execution_score = 0.0
            old.cross_source_score = 0.0
            old.saturation_score = 0.0
            old.score_version = SCORING_MODEL_VERSION
            old.score_breakdown = {
                "model_version": SCORING_MODEL_VERSION,
                "reason": "opportunity no longer has an active qualifying cluster",
                "components": {"demand": 0.0, "supply": 0.0, "execution": 0.0, "cross_source": 0.0, "saturation": 0.0},
                "total": 0.0,
            }
            old.updated_at = now
            record_score_snapshot(db, old, now=now)
            processed_ids.add(old.id)

    # Pre-0.4 redundant rows can be removed only if they never accumulated user research.
    redundant = db.scalars(select(Opportunity).where(Opportunity.opportunity_key.like("keyword:%"), Opportunity.stage == "DORMANT")).all()
    for old in redundant:
        if db.get(OpportunityResearch, old.id) is not None:
            continue
        if db.scalar(select(OpportunityLineage.id).where(or_(OpportunityLineage.parent_opportunity_id == old.id, OpportunityLineage.child_opportunity_id == old.id))) is not None:
            continue
        db.execute(delete(OpportunityEvidence).where(OpportunityEvidence.opportunity_id == old.id))
        db.execute(delete(OpportunityKeyword).where(OpportunityKeyword.opportunity_id == old.id))
        db.delete(old)
        processed_ids.discard(old.id)
    db.flush()
    if progress_callback is not None:
        progress_callback()
    return processed_ids


def build_analysis_input_for_opportunity(db: Session, opportunity_id: int) -> OpportunityAnalysisInput:
    opp = db.get(Opportunity, opportunity_id)
    if opp is None:
        raise KeyError(f"unknown opportunity id: {opportunity_id}")
    keyword_rows = db.execute(
        select(OpportunityKeyword, Keyword)
        .join(Keyword, Keyword.id == OpportunityKeyword.keyword_id)
        .where(OpportunityKeyword.opportunity_id == opportunity_id)
        .order_by(OpportunityKeyword.role.desc(), OpportunityKeyword.weight.desc())
    ).all()
    evidence_rows = db.execute(
        select(OpportunityEvidence, NormalizedItem, RawObservation)
        .join(NormalizedItem, NormalizedItem.id == OpportunityEvidence.normalized_item_id)
        .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
        .where(OpportunityEvidence.opportunity_id == opportunity_id)
        .order_by(OpportunityEvidence.observed_at.desc())
    ).all()
    type_counts = Counter(ev.evidence_type for ev, _item, _raw in evidence_rows)
    bounded_rows = select_evidence_citations([
        {
            "evidence_id": evidence_id_for_content_hash(raw.content_hash),
            "source": item.source_id,
            "type": ev.evidence_type,
            "item_type": item.item_type,
            "quality": raw.evidence_quality,
            "acquisition_method": raw.acquisition_method,
            "provenance": provenance_from_payload(raw.raw_payload),
            "title": _bounded(item.title, 500),
            "text": _bounded(item.text, max(0, settings.analysis_evidence_text_chars)),
            "url": _bounded(item.source_url, 2_000),
            "observed_at": item.observed_at,
        }
        for ev, item, raw in evidence_rows
    ], limit=max(1, min(100, settings.analysis_evidence_limit)))
    return OpportunityAnalysisInput(
        title=opp.title,
        related_keywords=[kw.display_name for _link, kw in keyword_rows[:MAX_ANALYSIS_KEYWORDS]],
        stage=opp.stage,
        score=opp.score,
        risk_score=opp.risk_score,
        evidence_types=dict(type_counts),
        evidence=bounded_rows,
    )


def opportunity_detail(db: Session, opportunity_id: int, *, evidence_limit: int = 50, evidence_text_chars: int = 2_000) -> dict:
    opp = db.get(Opportunity, opportunity_id)
    if opp is None:
        raise KeyError(f"unknown opportunity id: {opportunity_id}")
    evidence = db.execute(
        select(OpportunityEvidence, NormalizedItem, RawObservation)
        .join(NormalizedItem, NormalizedItem.id == OpportunityEvidence.normalized_item_id)
        .join(RawObservation, RawObservation.id == NormalizedItem.raw_observation_id)
        .where(OpportunityEvidence.opportunity_id == opportunity_id)
        .order_by(OpportunityEvidence.observed_at.desc())
    ).all()
    keyword_rows = db.execute(
        select(OpportunityKeyword, Keyword)
        .join(Keyword, Keyword.id == OpportunityKeyword.keyword_id)
        .where(OpportunityKeyword.opportunity_id == opportunity_id)
        .order_by(OpportunityKeyword.role.desc(), OpportunityKeyword.weight.desc())
    ).all()
    versions = db.scalars(
        select(OpportunityClusterVersion).where(OpportunityClusterVersion.opportunity_id == opportunity_id).order_by(OpportunityClusterVersion.generation.desc()).limit(20)
    ).all()
    lineage = db.execute(
        select(OpportunityLineage).where(or_(OpportunityLineage.parent_opportunity_id == opportunity_id, OpportunityLineage.child_opportunity_id == opportunity_id)).order_by(OpportunityLineage.created_at.desc())
    ).scalars().all()

    now = utc_now()
    type_counts = Counter(ev.evidence_type for ev, _item, _raw in evidence)
    source_counts = Counter(item.source_id for _ev, item, _raw in evidence)
    quality_counts = Counter(raw.evidence_quality for _ev, _item, raw in evidence)
    recent_7d = sum(1 for ev, _item, _raw in evidence if ev.observed_at >= now - timedelta(days=7))
    recent_30d = sum(1 for ev, _item, _raw in evidence if ev.observed_at >= now - timedelta(days=30))
    average_weight = round(sum(ev.weight for ev, _item, _raw in evidence) / len(evidence), 3) if evidence else 0.0
    citation_rows = [{
        "evidence_id": evidence_id_for_content_hash(raw.content_hash),
        "type": ev.evidence_type,
        "weight": ev.weight,
        "quality": raw.evidence_quality,
        "acquisition_method": raw.acquisition_method,
        "provenance": provenance_from_payload(raw.raw_payload),
        "source": item.source_id,
        "item_type": item.item_type,
        "title": _bounded(item.title, 500),
        "text": _bounded(item.text, max(0, evidence_text_chars)),
        "url": _bounded(item.source_url, 2_000),
        "observed_at": item.observed_at,
    } for ev, item, raw in evidence]
    bound = bind_citation_selection(
        citation_rows,
        binding_type="opportunity",
        binding_id=opp.id,
        limit=max(1, min(100, evidence_limit)),
    )
    limited = bound["citations"]
    research = db.get(OpportunityResearch, opportunity_id)

    return {
        "id": opp.id,
        "opportunity_key": opp.opportunity_key,
        "title": opp.title,
        "stage": opp.stage,
        "score": opp.score,
        "score_version": opp.score_version,
        "score_breakdown": opp.score_breakdown,
        "risk_score": opp.risk_score,
        "scores": {"demand": opp.demand_score, "supply": opp.supply_score, "execution": opp.execution_score, "cross_source": opp.cross_source_score, "saturation": opp.saturation_score},
        "cluster": {
            "signature": opp.cluster_signature,
            "generation": opp.cluster_generation,
            "versions": [{"generation": v.generation, "signature": v.cluster_signature, "keyword_ids": v.keyword_ids, "change_type": v.change_type, "started_at": v.started_at, "ended_at": v.ended_at} for v in versions],
            "lineage": [{"parent_opportunity_id": row.parent_opportunity_id, "child_opportunity_id": row.child_opportunity_id, "relation_type": row.relation_type, "created_at": row.created_at} for row in lineage],
        },
        "analysis": {
            "status": opp.analysis_status, "provider": opp.analysis_provider, "analyzed_at": opp.analyzed_at,
            "attempt_count": opp.analysis_attempt_count, "last_attempt_at": opp.analysis_last_attempt_at,
            "next_retry_at": opp.analysis_next_retry_at, "summary": opp.summary, "target_user": opp.target_user,
            "business_model": opp.business_model, "monetization": opp.monetization, "risk_notes": opp.risk_notes, "error": opp.analysis_error,
            "citation_contract_version": CITATION_CONTRACT_VERSION,
            "citations": opp.analysis_citations or [],
            "conflict": opp.analysis_conflict or {},
        },
        "keywords": [{"id": kw.id, "keyword": kw.display_name, "role": link.role, "weight": link.weight} for link, kw in keyword_rows],
        "evidence_count": opp.evidence_count,
        "evidence_contract": {"version": CITATION_CONTRACT_VERSION, "id_algorithm": "sha256-content-hash-v1"},
        "evidence_binding": bound["binding"],
        "evidence_summary": {"stored": len(evidence), "returned": len(limited), "types": dict(type_counts), "sources": dict(source_counts), "qualities": dict(quality_counts), "recent_7d": recent_7d, "recent_30d": recent_30d, "average_quality_weight": average_weight},
        "research": {"status": research.status if research else "NEW", "starred": research.starred if research else False, "priority": research.priority if research else 0, "notes": research.notes if research else "", "tags": (research.tags or []) if research else [], "updated_at": research.updated_at if research else None},
        "first_seen_at": opp.first_seen_at,
        "last_seen_at": opp.last_seen_at,
        "evidence": limited,
    }
