from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_security_gate import run_security_gate  # noqa: E402


def test_security_gate_is_green_across_all_review_domains():
    result = run_security_gate()
    assert result["status"] == "PASS"
    assert all(result["checks"].values())
    assert result["summary"]["security_controls"] == 30
    assert result["summary"]["real_data_collected"] == 0
