#!/usr/bin/env python3
"""Validate the product functional matrix and its traceable test targets."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "validation" / "functional_matrix.json"
REQUIRED_AREAS = {"Observation", "Keyword", "Trend", "Graph", "Opportunity", "Alert", "Delivery", "Enterprise", "Security", "Operations"}
TRACE_ID_RE = re.compile(r"^FM-[A-Z]+-\d{3}$")
ALLOWED_DATA_CLASSES = {"SYNTHETIC", "MOCK"}
REQUIRED_FIELDS = {"trace_id", "area", "capability", "input_contract", "output_contract", "state", "test_file", "data_class"}


def validate_matrix(path: Path = MATRIX_PATH) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("matrix_id") != "opportunity-radar-functional-matrix":
        raise ValueError("matrix_id is invalid")
    if payload.get("data_policy") != "SYNTHETIC_OR_MOCK_ONLY":
        raise ValueError("matrix data policy must be SYNTHETIC_OR_MOCK_ONLY")
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) < 20:
        raise ValueError("functional matrix must contain at least 20 rows")
    trace_ids: set[str] = set()
    areas: set[str] = set()
    for index, row in enumerate(rows, start=1):
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            raise ValueError(f"row {index} is missing fields: {sorted(missing)}")
        trace_id = str(row["trace_id"])
        if not TRACE_ID_RE.fullmatch(trace_id) or trace_id in trace_ids:
            raise ValueError(f"row {index} has an invalid or duplicate trace_id: {trace_id}")
        trace_ids.add(trace_id)
        areas.add(str(row["area"]))
        if row["data_class"] not in ALLOWED_DATA_CLASSES:
            raise ValueError(f"row {trace_id} uses an unsafe data class")
        test_file = ROOT / str(row["test_file"])
        if not test_file.is_file() or "backend/tests" not in test_file.as_posix():
            raise ValueError(f"row {trace_id} test target does not exist: {row['test_file']}")
        for field in ("capability", "input_contract", "output_contract", "state"):
            if not str(row[field]).strip() or any(marker in str(row[field]).upper() for marker in ("TODO", "FIXME")):
                raise ValueError(f"row {trace_id} has an incomplete {field}")
    missing_areas = REQUIRED_AREAS - areas
    if missing_areas:
        raise ValueError(f"functional matrix is missing areas: {sorted(missing_areas)}")
    return {"matrix_id": payload["matrix_id"], "matrix_version": payload.get("matrix_version"), "rows": len(rows), "areas": sorted(areas)}


def main() -> int:
    try:
        result = validate_matrix()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FUNCTIONAL_MATRIX_FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"FUNCTIONAL_MATRIX_PASS: {result['rows']} rows across {len(result['areas'])} areas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
