from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_false_completion_fixes import validate_fix_ledger  # noqa: E402


def test_false_completion_fix_ledger_confirms_each_item():
    result = validate_fix_ledger(
        Path(__file__).parents[2] / "validation" / "false_completion_fix_ledger.json",
        Path(__file__).parents[2] / "validation" / "false_completion_scan.json",
    )
    assert result["entries"] == 9
    assert result["scan_violations"] == 0
    assert result["status_counts"]["FIXED"] == 2
    assert result["status_counts"]["EXPLICIT_CONTRACT"] == 4
