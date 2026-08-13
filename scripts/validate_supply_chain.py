from __future__ import annotations

import importlib.metadata as metadata
import json
import re
import hashlib
import subprocess
from pathlib import Path
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]


def parse_lock(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^;\s]+)", line)
        if not match:
            raise AssertionError(f"not exactly locked: {path}: {line}")
        result[canonicalize_name(match.group(1))] = match.group(2)
    return result


def main() -> int:
    dev = parse_lock(ROOT / "backend" / "requirements-dev.lock")
    prod = parse_lock(ROOT / "backend" / "requirements-prod.lock")
    for name, expected in dev.items():
        actual = metadata.version(name)
        assert actual == expected, f"development lock mismatch {name}: expected {expected}, got {actual}"
    assert prod["psycopg"] == prod["psycopg-binary"]
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "requirements-prod.lock" in dockerfile and "requirements-prod.txt ./requirements.txt" not in dockerfile
    package = json.loads((ROOT / "frontend" / "package-lock.json").read_text(encoding="utf-8"))
    assert package["packages"]["node_modules/typescript"]["version"] == "5.8.3"
    tsc = subprocess.check_output(["tsc", "--version"], text=True).strip()
    assert tsc == "Version 5.8.3", tsc
    sbom = json.loads((ROOT / "sbom.cyclonedx.json").read_text(encoding="utf-8"))
    purls = {row["purl"] for row in sbom["components"]}
    for name, version in prod.items():
        assert f"pkg:pypi/{name}@{version}" in purls
    assert "pkg:npm/typescript@5.8.3" in purls
    expected_fingerprint = hashlib.sha256("\n".join(sorted(purls)).encode("utf-8")).hexdigest()
    properties = {row.get("name"): row.get("value") for row in sbom.get("metadata", {}).get("properties", [])}
    assert properties.get("opportunity-radar:dependency-fingerprint") == expected_fingerprint, "SBOM dependency fingerprint is stale"
    assert sbom.get("metadata", {}).get("component", {}).get("version") == "0.8.0", "SBOM application version is stale"
    print(f"SUPPLY_CHAIN_PASS dev_packages={len(dev)} prod_packages={len(prod)} sbom_components={len(purls)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
