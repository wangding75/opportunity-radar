#!/usr/bin/env python3
"""Generate an evidence-driven functional coverage report.

The matrix describes intended coverage.  It is not, by itself, proof that a
feature ran successfully.  Runtime, PostgreSQL and external evidence must be
recorded separately before a row can move beyond STATIC_ONLY.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from scan_functional_matrix_gaps import scan_gaps
from validate_false_completion import scan_false_completion
from validate_functional_matrix import MATRIX_PATH, ROOT, validate_matrix
from validate_traceability import TRACEABILITY_PATH, validate_traceability


REPORT_JSON_PATH = ROOT / "validation" / "functional_audit_report.json"
REPORT_MARKDOWN_PATH = ROOT / "docs" / "FUNCTIONAL_AUDIT_REPORT.md"
EVIDENCE_PATH = ROOT / "validation" / "functional_validation_evidence.json"
NA_PREFIX = "N/A - "
VALID_COVERAGE_STATUSES = {
    "NOT_CHECKED",
    "STATIC_ONLY",
    "TESTED",
    "RUNTIME_VERIFIED",
    "EXTERNAL_VERIFIED",
}
LAYER_NAMES = (
    "static_completion_hygiene",
    "runtime_functional_validation",
    "real_postgresql_validation",
    "external_integration_validation",
    "production_readiness",
)
EVIDENCE_LAYER_STATUSES = {"PASS", "NOT_CHECKED", "TESTED", "RUNTIME_VERIFIED", "EXTERNAL_VERIFIED", "NOT_READY", "READY"}


def _linked(targets: list[str]) -> bool:
    return bool(targets) and not all(target.startswith(NA_PREFIX) for target in targets)


def _status(targets: list[str]) -> str:
    return "LINKED" if _linked(targets) else "N/A (explicit)"


def _load_evidence(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("evidence_schema_version") != "1.0":
        raise ValueError("functional validation evidence schema is invalid")
    layers = payload.get("layers")
    if not isinstance(layers, dict) or set(layers) != set(LAYER_NAMES):
        raise ValueError("functional validation evidence must define all validation layers")
    for layer_name in LAYER_NAMES:
        layer = layers[layer_name]
        if not isinstance(layer, dict) or layer.get("status") not in EVIDENCE_LAYER_STATUSES:
            raise ValueError(f"invalid evidence status for layer {layer_name}")
        sources = layer.get("sources", [])
        if not isinstance(sources, list) or not all(isinstance(source, str) and source.strip() for source in sources):
            raise ValueError(f"invalid evidence sources for layer {layer_name}")
        for source in sources:
            if source.startswith(("http://", "https://")):
                continue
            if not (ROOT / source).is_file():
                raise ValueError(f"evidence source does not exist: {source}")
    real_data_collected = payload.get("real_data_collected", 0)
    if not isinstance(real_data_collected, int) or real_data_collected < 0:
        raise ValueError("real_data_collected must be a non-negative integer")
    row_evidence = payload.get("rows", {})
    if not isinstance(row_evidence, dict):
        raise ValueError("row evidence must be an object")
    for trace_id, evidence in row_evidence.items():
        if not isinstance(trace_id, str) or not isinstance(evidence, dict):
            raise ValueError("row evidence keys and values must be objects")
        if evidence.get("status") not in VALID_COVERAGE_STATUSES:
            raise ValueError(f"invalid evidence status for row {trace_id}")
        sources = evidence.get("sources", [])
        if not isinstance(sources, list) or not all(isinstance(source, str) and source.strip() for source in sources):
            raise ValueError(f"invalid evidence sources for row {trace_id}")
        for source in sources:
            if source.startswith(("http://", "https://")):
                continue
            if not (ROOT / source).is_file():
                raise ValueError(f"row evidence source does not exist: {source}")
        if evidence["status"] == "EXTERNAL_VERIFIED" and real_data_collected == 0:
            raise ValueError(f"row {trace_id} cannot be externally verified without real data")
    if layers["external_integration_validation"]["status"] == "EXTERNAL_VERIFIED" and real_data_collected == 0:
        raise ValueError("external integration validation cannot be verified without real data")
    return payload


def _effective_layer_status(evidence: dict, scan: dict) -> dict[str, dict]:
    layers = evidence["layers"]
    static_scan_status = "PASS" if scan["status"] == "PASS" and scan["violation_count"] == 0 else "FAIL"
    return {
        name: {
            "status": static_scan_status if name == "static_completion_hygiene" else layers[name]["status"],
            "sources": list(layers[name].get("sources", [])),
        }
        for name in LAYER_NAMES
    }


def _production_readiness(layers: dict[str, dict], gap_scan: dict, real_data_collected: int) -> dict:
    reasons: list[str] = []
    if layers["static_completion_hygiene"]["status"] != "PASS":
        reasons.append("false-completion hygiene is not green")
    if gap_scan["gap_count"]:
        reasons.append(f"{gap_scan['gap_count']} declared functional chain gaps remain")
    if layers["runtime_functional_validation"]["status"] not in {"TESTED", "RUNTIME_VERIFIED", "EXTERNAL_VERIFIED"}:
        reasons.append("runtime functional evidence is not recorded")
    if layers["real_postgresql_validation"]["status"] not in {"RUNTIME_VERIFIED", "EXTERNAL_VERIFIED"}:
        reasons.append("real PostgreSQL evidence is not recorded")
    if layers["external_integration_validation"]["status"] != "EXTERNAL_VERIFIED" or real_data_collected == 0:
        reasons.append("external integration evidence is not recorded with real data")
    return {
        "status": "READY" if not reasons else "NOT_READY",
        "sources": layers["production_readiness"]["sources"],
        "reasons": reasons,
    }


def build_report(evidence_path: Path = EVIDENCE_PATH) -> dict:
    matrix_validation = validate_matrix()
    traceability_validation = validate_traceability()
    gap_scan = scan_gaps()
    evidence = _load_evidence(evidence_path)
    false_completion_scan = scan_false_completion()
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    traceability = json.loads(TRACEABILITY_PATH.read_text(encoding="utf-8"))
    rows_by_id = {str(row["trace_id"]): row for row in matrix["rows"]}
    layers = _effective_layer_status(evidence, false_completion_scan)
    static_sources = layers["static_completion_hygiene"]["sources"]

    report_rows: list[dict] = []
    na_exceptions: list[dict[str, str]] = []
    evidence_rows = evidence.get("rows", {})
    for entry in traceability["entries"]:
        trace_id = str(entry["trace_id"])
        matrix_row = rows_by_id[trace_id]
        flags = {
            "code": _linked(entry["code_targets"]),
            "api": _linked(entry["api_targets"]),
            "ui": _linked(entry["ui_targets"]),
            "worker": _linked(entry["worker_targets"]),
            "tests": _linked(entry["test_targets"]),
            "docs": _linked(entry["docs_targets"]),
        }
        for field in ("api_targets", "ui_targets", "worker_targets"):
            if not flags[field.removesuffix("_targets")]:
                na_exceptions.append({"trace_id": trace_id, "field": field, "reason": entry[field][0]})
        row_evidence = evidence_rows.get(trace_id)
        coverage_status = row_evidence["status"] if row_evidence else ("STATIC_ONLY" if static_sources and layers["static_completion_hygiene"]["status"] == "PASS" else "NOT_CHECKED")
        evidence_sources = list(row_evidence.get("sources", [])) if row_evidence else list(static_sources)
        report_rows.append(
            {
                "trace_id": trace_id,
                "area": matrix_row["area"],
                "capability": matrix_row["capability"],
                "data_class": matrix_row["data_class"],
                "input_contract": matrix_row["input_contract"],
                "output_contract": matrix_row["output_contract"],
                "state": matrix_row["state"],
                "code_targets": entry["code_targets"],
                "api_targets": entry["api_targets"],
                "ui_targets": entry["ui_targets"],
                "worker_targets": entry["worker_targets"],
                "test_targets": entry["test_targets"],
                "docs_targets": entry["docs_targets"],
                "evidence": entry["evidence"],
                "evidence_sources": evidence_sources,
                "coverage": {
                    "status": coverage_status,
                    "code": _status(entry["code_targets"]),
                    "api": _status(entry["api_targets"]),
                    "ui": _status(entry["ui_targets"]),
                    "worker": _status(entry["worker_targets"]),
                    "tests": _status(entry["test_targets"]),
                    "docs": _status(entry["docs_targets"]),
                },
            }
        )

    areas = sorted({row["area"] for row in report_rows})
    area_summary = []
    for area in areas:
        area_rows = [row for row in report_rows if row["area"] == area]
        area_summary.append(
            {
                "area": area,
                "rows": len(area_rows),
                "status_counts": dict(sorted(Counter(row["coverage"]["status"] for row in area_rows).items())),
                "data_classes": dict(sorted(Counter(row["data_class"] for row in area_rows).items())),
            }
        )

    link_counts = {
        field: sum(row["coverage"][field] == "LINKED" for row in report_rows)
        for field in ("code", "api", "ui", "worker", "tests", "docs")
    }
    report_status = "PASS" if (
        matrix_validation["rows"] == traceability_validation["entries"]
        and gap_scan["gap_count"] == 0
        and false_completion_scan["status"] == "PASS"
        and false_completion_scan["violation_count"] == 0
    ) else "FAIL"
    readiness = _production_readiness(layers, gap_scan, evidence["real_data_collected"])
    return {
        "report_id": "opportunity-radar-functional-audit",
        "report_version": "2.0",
        "report_status": report_status,
        "report_status_meaning": "evidence/report-integrity status; it is not a claim that every capability is production-ready",
        "generated_from": {
            "matrix": "validation/functional_matrix.json",
            "traceability": "validation/functional_traceability.json",
            "gap_scanner": "scripts/scan_functional_matrix_gaps.py",
            "evidence": evidence_path.relative_to(ROOT).as_posix(),
            "false_completion_scan": "validation/false_completion_scan.json",
        },
        "data_policy": matrix["data_policy"],
        "real_data_collected": evidence["real_data_collected"],
        "validation_layers": layers,
        "production_readiness": readiness,
        "summary": {
            "matrix_rows": matrix_validation["rows"],
            "traceability_entries": traceability_validation["entries"],
            "areas": len(areas),
            "gap_count": gap_scan["gap_count"],
            "reverse_unregistered_count": gap_scan["reverse_unregistered_count"],
            "coverage_status_counts": dict(sorted(Counter(row["coverage"]["status"] for row in report_rows).items())),
            "static_only_rows": sum(row["coverage"]["status"] == "STATIC_ONLY" for row in report_rows),
            "link_counts": link_counts,
            "data_classes": dict(sorted(Counter(row["data_class"] for row in report_rows).items())),
        },
        "reverse_coverage": gap_scan["reverse_coverage"],
        "area_summary": area_summary,
        "na_exceptions": na_exceptions,
        "rows": report_rows,
    }


def _markdown(report: dict) -> str:
    summary = report["summary"]
    counts = summary["link_counts"]
    layers = report["validation_layers"]
    lines = [
        "# Functional audit coverage report",
        "",
        "This report separates matrix/static evidence from runtime, real PostgreSQL, external-integration and production-readiness evidence.",
        "A static PASS is not functional completion. A row advances only when evidence is recorded in `validation/functional_validation_evidence.json`.",
        "",
        f"- Report integrity status: **{report['report_status']}**",
        f"- Production readiness: **{report['production_readiness']['status']}**",
        f"- Matrix rows / traceability entries: **{summary['matrix_rows']} / {summary['traceability_entries']}**",
        f"- Functional chain gaps: **{summary['gap_count']}**",
        f"- Unregistered important implementation targets: **{summary['reverse_unregistered_count']}**",
        f"- Real data collected for validation: **{report['real_data_collected']}**",
        f"- Data classes: **{', '.join(f'{key}={value}' for key, value in summary['data_classes'].items())}**",
        "",
        "## Validation layers",
        "",
        "| Layer | Status | Evidence sources |",
        "| --- | --- | --- |",
    ]
    for name in LAYER_NAMES:
        layer = layers[name]
        lines.append(f"| {name} | `{layer['status']}` | {', '.join(f'`{source}`' for source in layer['sources']) or 'none recorded'} |")
    lines.extend(["", "Production readiness reasons:"])
    lines.extend(f"- {reason}" for reason in report["production_readiness"]["reasons"] or ["all required evidence layers are verified"])
    lines.extend([
        "",
        "## Chain coverage",
        "",
        "| Link | Rows with a real target |",
        "| --- | ---: |",
    ])
    lines.extend(f"| {field} | {counts[field]} / {summary['matrix_rows']} |" for field in ("code", "api", "ui", "worker", "tests", "docs"))
    lines.extend(["", "## Area coverage", "", "| Area | Rows | Coverage statuses | Data classes |", "| --- | ---: | --- | --- |"])
    for row in report["area_summary"]:
        statuses = ", ".join(f"{key}={value}" for key, value in row["status_counts"].items())
        classes = ", ".join(f"{key}={value}" for key, value in row["data_classes"].items())
        lines.append(f"| {row['area']} | {row['rows']} | {statuses} | {classes} |")
    lines.extend(["", "## Reverse coverage findings", "", "The following important API modules, connectors, core services or workers are not registered by a matrix traceability entry. This is an explicit review finding, not a hidden success state.", ""])
    reverse_findings = [finding for findings in report["reverse_coverage"].values() for finding in findings]
    if reverse_findings:
        lines.extend(["| Kind | Target | Reason |", "| --- | --- | --- |"])
        lines.extend(f"| {finding['kind']} | `{finding['target']}` | {finding['reason']} |" for finding in reverse_findings)
    else:
        lines.append("None.")
    lines.extend(["", "## Explicit N/A exceptions", "", "These are intentional backend-only, internal-contract or isolated-Mock links; they are not counted as functional chain gaps.", ""])
    if report["na_exceptions"]:
        lines.extend(["| Trace ID | Link | Reason |", "| --- | --- | --- |"])
        lines.extend(f"| {row['trace_id']} | {row['field']} | {row['reason']} |" for row in report["na_exceptions"])
    else:
        lines.append("None.")
    lines.extend(["", "## Evidence rows", "", "| Trace ID | Area | Capability | Coverage status | Data | Evidence sources |", "| --- | --- | --- | --- | --- | --- |"])
    for row in report["rows"]:
        sources = ", ".join(f"`{source}`" for source in row["evidence_sources"]) or "none recorded"
        lines.append(f"| {row['trace_id']} | {row['area']} | {row['capability']} | `{row['coverage']['status']}` | `{row['data_class']}` | {sources} |")
    lines.extend(["", "The complete file-level targets and evidence-derived statuses are in `validation/functional_audit_report.json`. The current matrix policy permits only SYNTHETIC or MOCK validation data; it does not establish production readiness.", ""])
    return "\n".join(lines)


def write_report(report: dict) -> None:
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MARKDOWN_PATH.write_text(_markdown(report), encoding="utf-8")


def main() -> int:
    try:
        report = build_report()
        write_report(report)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FUNCTIONAL_AUDIT_REPORT_FAIL: {exc}", file=sys.stderr)
        return 1
    if report["report_status"] != "PASS":
        print(f"FUNCTIONAL_AUDIT_REPORT_FAIL: report integrity status is {report['report_status']}", file=sys.stderr)
        return 1
    print(
        "FUNCTIONAL_AUDIT_REPORT_PASS: "
        f"{report['summary']['matrix_rows']} rows, "
        f"{report['summary']['gap_count']} chain gaps, "
        f"{report['summary']['static_only_rows']} static-only rows, "
        f"production_readiness={report['production_readiness']['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
