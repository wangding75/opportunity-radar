from __future__ import annotations

import json
import re
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
LOCKS = [ROOT / "backend" / "requirements-prod.lock", ROOT / "frontend" / "package-lock.json"]


def python_components(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^;\s]+)", line)
        if not match:
            raise ValueError(f"unlocked Python dependency: {line}")
        name, version = match.groups()
        rows.append({"type": "library", "name": name, "version": version, "purl": f"pkg:pypi/{canonicalize_name(name)}@{version}"})
    return rows


def frontend_components(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for key, meta in data.get("packages", {}).items():
        if not key.startswith("node_modules/"):
            continue
        name = key[len("node_modules/"):]
        version = meta.get("version")
        if not version:
            raise ValueError(f"unlocked frontend package: {name}")
        rows.append({"type": "library", "name": name, "version": version, "purl": f"pkg:npm/{name}@{version}"})
    return rows


def main() -> int:
    components = python_components(LOCKS[0]) + frontend_components(LOCKS[1])
    components.sort(key=lambda x: (x["purl"]))
    fingerprint = hashlib.sha256("\n".join(item["purl"] for item in components).encode("utf-8")).hexdigest()
    serial = uuid.uuid5(uuid.NAMESPACE_URL, "opportunity-radar:" + fingerprint)
    payload = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{serial}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "component": {"type": "application", "name": "opportunity-radar", "version": "0.8.0"},
            "properties": [{"name": "opportunity-radar:dependency-fingerprint", "value": fingerprint}],
        },
        "components": components,
    }
    out = ROOT / "sbom.cyclonedx.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"SBOM_GENERATED components={len(components)} path={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
