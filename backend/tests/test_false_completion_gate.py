from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_false_completion_gate import run_gate  # noqa: E402


def test_false_completion_regression_gate_is_green():
    result = run_gate()
    assert result["status"] == "PASS"
    assert all(result["checks"].values())
    assert result["summary"]["scan_violations"] == 0
    assert result["summary"]["functional_gaps"] == 0
