from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_false_completion import scan_false_completion  # noqa: E402


def test_false_completion_ruleset_has_no_unapproved_violations():
    result = scan_false_completion(Path(__file__).parents[2] / "validation" / "false_completion_rules.json")
    assert result["status"] == "PASS"
    assert result["violation_count"] == 0
    assert result["scanned_files"] >= 20
