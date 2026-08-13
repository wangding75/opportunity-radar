from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_frontend_rbac import validate_frontend_rbac  # noqa: E402


def test_compiled_frontend_rbac_matches_backend_route_contracts():
    report = validate_frontend_rbac()
    assert report["status"] == "PASS"
    assert all(report["checks"].values())
    assert report["summary"]["real_data_collected"] == 0
