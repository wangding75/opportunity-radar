#!/usr/bin/env python3
"""Validate dependency and software supply-chain review evidence."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "validation" / "security_review_dependency_supply_chain.json"
REQUIRED_CONTROLS = {f"DEPEND-{index:03d}" for index in range(1, 7)}
LOCK_LINE = re.compile(r"^[A-Za-z0-9_.-]+==[^;\s]+$")


def _pinned_lock(path: Path) -> int:
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not LOCK_LINE.fullmatch(line):
            raise ValueError(f"dependency lock contains an unpinned line: {path}: {line}")
        count += 1
    if not count:
        raise ValueError(f"dependency lock is empty: {path}")
    return count


def validate_dependency_review(path: Path = REVIEW_PATH) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("review_id") != "opportunity-radar-dependency-supply-chain-review":
        raise ValueError("dependency review ID is invalid")
    if payload.get("data_policy") != "SYNTHETIC_OR_MOCK_ONLY" or payload.get("real_data_collected") != 0:
        raise ValueError("dependency review must be SYNTHETIC/MOCK-only with zero real data")
    controls = payload.get("controls")
    if not isinstance(controls, list):
        raise ValueError("dependency review controls must be a list")
    ids: set[str] = set()
    for control in controls:
        required = {"control_id", "control", "status", "code_targets", "test_targets", "evidence"}
        if not isinstance(control, dict) or required - set(control):
            raise ValueError("dependency review control is incomplete")
        control_id = str(control["control_id"])
        if control_id in ids or control["status"] != "PASS":
            raise ValueError(f"dependency review control is duplicate or not PASS: {control_id}")
        ids.add(control_id)
        for field in ("code_targets", "test_targets"):
            targets = control[field]
            if not isinstance(targets, list) or not targets:
                raise ValueError(f"{control_id} {field} must be a non-empty list")
            for target in targets:
                if not (ROOT / str(target)).is_file():
                    raise ValueError(f"{control_id} target does not exist: {target}")
        if not str(control["evidence"]).strip():
            raise ValueError(f"{control_id} has incomplete evidence")
    if ids != REQUIRED_CONTROLS:
        raise ValueError(f"dependency review control set mismatch: {sorted(ids)}")
    prod_count = _pinned_lock(ROOT / "backend" / "requirements-prod.lock")
    dev_count = _pinned_lock(ROOT / "backend" / "requirements-dev.lock")
    package_lock = json.loads((ROOT / "frontend" / "package-lock.json").read_text(encoding="utf-8"))
    package_rows = package_lock.get("packages", {})
    if not package_rows.get("node_modules/typescript", {}).get("version"):
        raise ValueError("frontend package-lock does not pin TypeScript")
    sbom = json.loads((ROOT / "sbom.cyclonedx.json").read_text(encoding="utf-8"))
    purls = {row.get("purl") for row in sbom.get("components", [])}
    if not purls or "pkg:npm/typescript@5.8.3" not in purls:
        raise ValueError("SBOM is missing expected locked frontend component")
    expected_fingerprint = hashlib.sha256("\n".join(sorted(purls)).encode("utf-8")).hexdigest()
    properties = {row.get("name"): row.get("value") for row in sbom.get("metadata", {}).get("properties", [])}
    if properties.get("opportunity-radar:dependency-fingerprint") != expected_fingerprint:
        raise ValueError("SBOM dependency fingerprint is stale")
    if payload.get("status") != "PASS":
        raise ValueError("dependency review status is not PASS")
    return {"review_id": payload["review_id"], "controls": len(controls), "production_lock": prod_count, "development_lock": dev_count, "sbom_components": len(purls), "status": payload["status"]}


def main() -> int:
    try:
        result = validate_dependency_review()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"DEPENDENCY_REVIEW_FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"DEPENDENCY_REVIEW_PASS: {result['controls']} controls, prod_lock={result['production_lock']}, dev_lock={result['development_lock']}, sbom={result['sbom_components']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
