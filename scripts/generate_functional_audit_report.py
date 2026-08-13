#!/usr/bin/env python3
"""Generate a deterministic, auditable functional coverage report."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from scan_functional_matrix_gaps import scan_gaps
from validate_functional_matrix import MATRIX_PATH, validate_matrix
from validate_traceability import ROOT, TRACEABILITY_PATH, validate_traceability


REPORT_JSON_PATH = ROOT / "validation" / "functional_audit_report.json"
REPORT_MARKDOWN_PATH = ROOT / "docs" / "FUNCTIONAL_AUDIT_REPORT.md"
NA_PREFIX = "N/A - "


def _linked(targets: list[str]) -> bool:
    return bool(targets) and not all(target.startswith(NA_PREFIX) for target in targets)


def _status(targets: list[str]) -> str:
    return "LINKED" if _linked(targets) else "N/A (explicit)"


def build_report() -> dict:
    matrix_validation = validate_matrix()
    traceability_validation = validate_traceability()
    gap_scan = scan_gaps()
    if gap_scan["gap_count"]:
        raise ValueError(f"cannot publish an audit report with {gap_scan['gap_count']} functional gaps")
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    traceability = json.loads(TRACEABILITY_PATH.read_text(encoding="utf-8"))
    rows_by_id = {str(row["trace_id"]): row for row in matrix["rows"]}

    report_rows: list[dict] = []
    na_exceptions: list[dict[str, str]] = []
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
                "coverage": {
                    "status": "COMPLETE",
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
                "complete_rows": sum(row["coverage"]["status"] == "COMPLETE" for row in area_rows),
                "data_classes": dict(sorted(Counter(row["data_class"] for row in area_rows).items())),
            }
        )

    link_counts = {
        field: sum(row["coverage"][field] == "LINKED" for row in report_rows)
        for field in ("code", "api", "ui", "worker", "tests", "docs")
    }
    return {
        "report_id": "opportunity-radar-functional-audit",
        "report_version": "1.0",
        "report_status": "PASS",
        "generated_from": {
            "matrix": "validation/functional_matrix.json",
            "traceability": "validation/functional_traceability.json",
            "gap_scanner": "scripts/scan_functional_matrix_gaps.py",
        },
        "data_policy": matrix["data_policy"],
        "real_data_collected": 0,
        "summary": {
            "matrix_rows": matrix_validation["rows"],
            "traceability_entries": traceability_validation["entries"],
            "areas": len(areas),
            "gap_count": gap_scan["gap_count"],
            "link_counts": link_counts,
            "data_classes": dict(sorted(Counter(row["data_class"] for row in report_rows).items())),
        },
        "area_summary": area_summary,
        "na_exceptions": na_exceptions,
        "rows": report_rows,
    }


def _markdown(report: dict) -> str:
    summary = report["summary"]
    counts = summary["link_counts"]
    lines = [
        "# Functional audit coverage report",
        "",
        "This deterministic report is generated from the functional matrix, the implementation traceability map and the zero-gap scanner.",
        "",
        f"- Status: **{report['report_status']}**",
        f"- Matrix rows / traceability entries: **{summary['matrix_rows']} / {summary['traceability_entries']}**",
        f"- Areas: **{summary['areas']}**",
        f"- Functional gaps: **{summary['gap_count']}**",
        f"- Real data collected for validation: **{report['real_data_collected']}**",
        f"- Data classes: **{', '.join(f'{key}={value}' for key, value in summary['data_classes'].items())}**",
        "",
        "## Chain coverage",
        "",
        "| Link | Rows with a real target |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {field} | {counts[field]} / {summary['matrix_rows']} |" for field in ("code", "api", "ui", "worker", "tests", "docs"))
    lines.extend(["", "## Area coverage", "", "| Area | Rows | Complete | Data classes |", "| --- | ---: | ---: | --- |"])
    for row in report["area_summary"]:
        classes = ", ".join(f"{key}={value}" for key, value in row["data_classes"].items())
        lines.append(f"| {row['area']} | {row['rows']} | {row['complete_rows']} | {classes} |")
    lines.extend(["", "## Explicit N/A exceptions", "", "These are intentional backend-only, internal-contract or isolated-Mock links; they are not counted as functional gaps.", ""])
    if report["na_exceptions"]:
        lines.extend(["| Trace ID | Link | Reason |", "| --- | --- | --- |"])
        lines.extend(f"| {row['trace_id']} | {row['field']} | {row['reason']} |" for row in report["na_exceptions"])
    else:
        lines.append("None.")
    lines.extend(["", "## Evidence rows", "", "| Trace ID | Area | Capability | State | Data | Test evidence |", "| --- | --- | --- | --- | --- | --- |"])
    for row in report["rows"]:
        tests = ", ".join(f"`{target}`" for target in row["test_targets"])
        lines.append(f"| {row['trace_id']} | {row['area']} | {row['capability']} | `{row['state']}` | `{row['data_class']}` | {tests} |")
    lines.extend(["", "The complete file-level code/API/UI/Worker/test/document targets are in `validation/functional_audit_report.json`. All rows use SYNTHETIC or MOCK validation data.", ""])
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
    print(f"FUNCTIONAL_AUDIT_REPORT_PASS: {report['summary']['matrix_rows']} rows, {report['summary']['gap_count']} gaps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
