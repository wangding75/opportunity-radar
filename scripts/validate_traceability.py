#!/usr/bin/env python3
"""Validate the feature-to-implementation traceability contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "validation" / "functional_matrix.json"
TRACEABILITY_PATH = ROOT / "validation" / "functional_traceability.json"
TRACE_ID_RE = re.compile(r"^FM-[A-Z]+-\d{3}$")
REQUIRED_FIELDS = {
    "trace_id",
    "data_class",
    "code_targets",
    "api_targets",
    "ui_targets",
    "worker_targets",
    "test_targets",
    "docs_targets",
    "evidence",
}
OPTIONAL_NA_FIELDS = ("api_targets", "ui_targets", "worker_targets")
NA_PREFIX = "N/A - "


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def _target_list(entry: dict, trace_id: str, field: str) -> list[str]:
    value = entry.get(field)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{trace_id} field {field} must be a non-empty string list")
    for item in value:
        normalized = item.strip()
        if not normalized or any(marker in normalized.upper() for marker in ("TODO", "FIXME")):
            raise ValueError(f"{trace_id} field {field} contains an incomplete target")
    return value


def _validate_file_targets(trace_id: str, field: str, targets: list[str], *, required_prefix: str | None = None) -> None:
    for target in targets:
        path = ROOT / target
        if not path.is_file():
            raise ValueError(f"{trace_id} {field} target does not exist: {target}")
        if required_prefix and not path.as_posix().startswith((ROOT / required_prefix).as_posix() + "/"):
            raise ValueError(f"{trace_id} {field} target must be under {required_prefix}: {target}")


def _validate_api_targets(trace_id: str, targets: list[str]) -> None:
    product_routes = _discover_product_routes()
    for target in targets:
        if target.startswith(NA_PREFIX):
            continue
        if not target.startswith("/") or " " in target:
            raise ValueError(f"{trace_id} API target must be an absolute route or explicit N/A: {target}")
        if target.startswith("/api/v1/") and target not in product_routes:
            raise ValueError(f"{trace_id} product API target is not registered: {target}")


def _discover_product_routes() -> set[str]:
    """Read product route decorators without importing the application."""
    routes: set[str] = set()
    router_pattern = re.compile(r"(?m)^\s*(\w+)\s*=\s*APIRouter\([^\n]*?prefix=[\"']([^\"']+)[\"']")
    decorator_pattern = re.compile(r"@(\w+)\.(?:get|post|patch|put|delete)\(\s*[\"']([^\"']+)[\"']")
    for api_file in (ROOT / "backend" / "app" / "api").glob("*.py"):
        source = api_file.read_text(encoding="utf-8")
        prefixes = {match.group(1): match.group(2) for match in router_pattern.finditer(source)}
        for match in decorator_pattern.finditer(source):
            prefix = prefixes.get(match.group(1))
            if prefix is None:
                continue
            route = match.group(2)
            routes.add(prefix.rstrip("/") + "/" + route.lstrip("/"))
    return routes


def _validate_optional_targets(trace_id: str, field: str, targets: list[str]) -> None:
    for target in targets:
        if target.startswith(NA_PREFIX):
            continue
        path = ROOT / target
        if not path.is_file():
            raise ValueError(f"{trace_id} {field} target does not exist: {target}")


def validate_traceability(
    matrix_path: Path = MATRIX_PATH,
    traceability_path: Path = TRACEABILITY_PATH,
) -> dict:
    matrix = _load_json(matrix_path)
    traceability = _load_json(traceability_path)
    if traceability.get("traceability_id") != "opportunity-radar-functional-traceability":
        raise ValueError("traceability_id is invalid")
    if traceability.get("source_matrix") != matrix_path.relative_to(ROOT).as_posix():
        raise ValueError("traceability source_matrix does not identify the functional matrix")
    if traceability.get("data_policy") != matrix.get("data_policy"):
        raise ValueError("traceability data policy must match the functional matrix")
    matrix_rows = matrix.get("rows")
    entries = traceability.get("entries")
    if not isinstance(matrix_rows, list) or not isinstance(entries, list):
        raise ValueError("matrix rows and traceability entries must both be lists")

    matrix_by_id = {str(row.get("trace_id")): row for row in matrix_rows}
    entry_ids: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"entry {index} must be an object")
        missing = REQUIRED_FIELDS - set(entry)
        if missing:
            raise ValueError(f"entry {index} is missing fields: {sorted(missing)}")
        trace_id = str(entry["trace_id"])
        if not TRACE_ID_RE.fullmatch(trace_id) or trace_id in entry_ids:
            raise ValueError(f"entry {index} has an invalid or duplicate trace_id: {trace_id}")
        if trace_id not in matrix_by_id:
            raise ValueError(f"entry {trace_id} is not present in the functional matrix")
        entry_ids.add(trace_id)
        matrix_row = matrix_by_id[trace_id]
        if entry["data_class"] != matrix_row.get("data_class"):
            raise ValueError(f"entry {trace_id} data class does not match the functional matrix")
        if not str(entry["evidence"]).strip() or any(marker in str(entry["evidence"]).upper() for marker in ("TODO", "FIXME")):
            raise ValueError(f"entry {trace_id} has incomplete evidence")

        targets = {field: _target_list(entry, trace_id, field) for field in REQUIRED_FIELDS if field.endswith("_targets")}
        _validate_file_targets(trace_id, "code_targets", targets["code_targets"])
        _validate_file_targets(trace_id, "test_targets", targets["test_targets"], required_prefix="backend/tests")
        _validate_file_targets(trace_id, "docs_targets", targets["docs_targets"], required_prefix="docs")
        matrix_test = str(matrix_row["test_file"])
        if matrix_test not in targets["test_targets"]:
            raise ValueError(f"entry {trace_id} does not include matrix test target: {matrix_test}")
        _validate_api_targets(trace_id, targets["api_targets"])
        for field in OPTIONAL_NA_FIELDS[1:]:
            _validate_optional_targets(trace_id, field, targets[field])

    missing_ids = set(matrix_by_id) - entry_ids
    extra_ids = entry_ids - set(matrix_by_id)
    if missing_ids or extra_ids:
        raise ValueError(f"traceability IDs differ from matrix; missing={sorted(missing_ids)}, extra={sorted(extra_ids)}")
    if len(entries) != len(matrix_rows):
        raise ValueError("traceability must contain exactly one entry for every functional matrix row")
    return {
        "traceability_id": traceability["traceability_id"],
        "version": traceability.get("traceability_version"),
        "entries": len(entries),
        "matrix_rows": len(matrix_rows),
    }


def main() -> int:
    try:
        result = validate_traceability()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"TRACEABILITY_FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"TRACEABILITY_PASS: {result['entries']} entries mapped to {result['matrix_rows']} matrix rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
