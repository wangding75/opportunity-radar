from __future__ import annotations

import re
from collections import Counter
from datetime import timedelta

from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Keyword, KeywordMention, NormalizedItem, SeedKeyword
from app.domain.enums import KeywordStatus

STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "your", "you", "are", "new", "最新", "工具",
    "软件", "教程", "系统", "一个", "可以", "使用", "相关", "项目", "平台",
    "负责", "进行", "支持", "提供", "以及", "通过", "内容", "功能",
    "招聘", "变现", "收益", "价格", "出售", "副业", "赚钱", "兼职", "教程", "素材",
}

_ascii_term = re.compile(r"(?<![\w-])[A-Za-z][A-Za-z0-9_+.-]{2,30}(?![\w-])")
_hash_term = re.compile(r"[#＃]([\w\u4e00-\u9fff-]{2,30})")
_mixed_phrase = re.compile(r"[A-Za-z0-9_+.-]*[\u4e00-\u9fff][A-Za-z0-9_+.\-\u4e00-\u9fff]{1,40}")
_connector_re = re.compile(r"(?:以及|并且|用于|通过|关于|负责|支持|提供|进行|和|与|及)")


def canonicalize_keyword(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _candidate_terms(text: str) -> list[str]:
    terms: list[str] = []
    terms.extend(_hash_term.findall(text))
    terms.extend(_ascii_term.findall(text))
    for chunk in _mixed_phrase.findall(text):
        for phrase in _connector_re.split(chunk):
            phrase = phrase.strip("._+- ")
            if 2 <= len(phrase) <= 16:
                terms.append(phrase)
    cleaned = []
    seen: set[str] = set()
    for term in terms:
        canonical = canonicalize_keyword(term)
        if not canonical or canonical in STOPWORDS or canonical.isdigit() or canonical in seen:
            continue
        seen.add(canonical)
        cleaned.append(term.strip())
    return cleaned


def discover_for_item(db: Session, item: NormalizedItem) -> list[Keyword]:
    text = f"{item.query} {item.title} {item.text}"
    terms = Counter(_candidate_terms(text))
    if item.query.strip():
        terms[item.query.strip()] += 3
    created_or_updated: list[Keyword] = []
    for display, _freq in terms.most_common(30):
        canonical = canonicalize_keyword(display)
        if len(canonical) < 2 or len(canonical) > 80 or canonical in STOPWORDS:
            continue
        kw = db.scalar(select(Keyword).where(Keyword.canonical == canonical))
        if kw is None:
            kw = Keyword(
                canonical=canonical,
                display_name=display,
                status=KeywordStatus.DISCOVERED.value,
                first_seen_at=item.observed_at,
                last_seen_at=item.observed_at,
            )
            db.add(kw)
            db.flush()
        mention = db.scalar(
            select(KeywordMention).where(
                KeywordMention.keyword_id == kw.id,
                KeywordMention.normalized_item_id == item.id,
            )
        )
        if mention is None:
            db.add(
                KeywordMention(
                    keyword_id=kw.id,
                    normalized_item_id=item.id,
                    source_id=item.source_id,
                    observed_at=item.observed_at,
                )
            )
        if item.observed_at > kw.last_seen_at:
            kw.last_seen_at = item.observed_at
        if item.observed_at < kw.first_seen_at:
            kw.first_seen_at = item.observed_at
        created_or_updated.append(kw)
    db.flush()
    return created_or_updated


def refresh_keyword_metrics(db: Session, keyword_ids: set[int] | None = None) -> None:
    now = utc_now()
    t7 = now - timedelta(days=7)
    t14 = now - timedelta(days=14)
    t30 = now - timedelta(days=30)

    aggregate_stmt = select(
            KeywordMention.keyword_id,
            func.count(KeywordMention.id).label("lifetime_obs"),
            func.count(distinct(KeywordMention.source_id)).label("lifetime_sources"),
            func.sum(case((KeywordMention.observed_at >= t7, 1), else_=0)).label("last_7"),
            func.sum(
                case((and_(KeywordMention.observed_at >= t14, KeywordMention.observed_at < t7), 1), else_=0)
            ).label("prev_7"),
            func.sum(case((KeywordMention.observed_at >= t30, 1), else_=0)).label("last_30"),
            func.count(distinct(case((KeywordMention.observed_at >= t7, KeywordMention.source_id), else_=None))).label(
                "sources_7"
            ),
            func.count(distinct(case((KeywordMention.observed_at >= t30, KeywordMention.source_id), else_=None))).label(
                "sources_30"
            ),
        ).group_by(KeywordMention.keyword_id)
    if keyword_ids is not None:
        aggregate_stmt = aggregate_stmt.where(KeywordMention.keyword_id.in_(keyword_ids))
    aggregate_rows = db.execute(aggregate_stmt).all()
    metrics = {row.keyword_id: row for row in aggregate_rows}

    seed_rows = db.scalars(select(SeedKeyword).where(SeedKeyword.enabled.is_(True))).all()
    seed_priorities = {row.canonical: row.priority for row in seed_rows}
    keyword_stmt = select(Keyword)
    if keyword_ids is not None:
        if not keyword_ids:
            return
        keyword_stmt = keyword_stmt.where(Keyword.id.in_(keyword_ids))
    keywords = db.scalars(keyword_stmt).all()
    for kw in keywords:
        row = metrics.get(kw.id)
        lifetime_obs = int(row.lifetime_obs or 0) if row else 0
        lifetime_sources = int(row.lifetime_sources or 0) if row else 0
        last_7 = int(row.last_7 or 0) if row else 0
        prev_7 = int(row.prev_7 or 0) if row else 0
        last_30 = int(row.last_30 or 0) if row else 0
        sources_7 = int(row.sources_7 or 0) if row else 0
        sources_30 = int(row.sources_30 or 0) if row else 0
        growth = (last_7 - prev_7) / max(prev_7, 1)

        score = min(
            100.0,
            last_7 * 3.0
            + last_30 * 0.5
            + sources_7 * 10.0
            + sources_30 * 4.0
            + min(lifetime_sources, 5) * 1.5
            + (max(growth, 0.0) * 10.0 if last_7 >= 2 else 0.0),
        )
        kw.observation_count = lifetime_obs
        kw.source_count = lifetime_sources
        kw.score = float(round(score, 2))

        stale_days = max(0, (now - kw.last_seen_at).days)
        age_days = max(0, (now - kw.first_seen_at).days)
        if stale_days > 90:
            kw.status = KeywordStatus.ARCHIVED.value
        elif stale_days > 30:
            kw.status = KeywordStatus.DECLINING.value
        elif sources_7 >= 2 and last_7 >= 5 and growth >= 0.3:
            kw.status = KeywordStatus.TRENDING.value
        elif last_30 >= 5 or sources_30 >= 2:
            kw.status = KeywordStatus.ACTIVE.value
        elif age_days <= 14 and last_30 > 0:
            kw.status = KeywordStatus.WATCHING.value
        elif last_30 > 0:
            kw.status = KeywordStatus.DISCOVERED.value
        else:
            kw.status = KeywordStatus.DECLINING.value

        if kw.canonical in seed_priorities:
            seed_floor = float(10 + seed_priorities[kw.canonical] * 5)
            kw.score = max(kw.score, seed_floor)
            if kw.status in {KeywordStatus.DECLINING.value, KeywordStatus.ARCHIVED.value, KeywordStatus.DISCOVERED.value}:
                kw.status = KeywordStatus.WATCHING.value
    db.flush()
