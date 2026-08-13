from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from generate_functional_audit_report import build_report  # noqa: E402


def test_functional_audit_report_is_complete_and_safe():
    report = build_report()
    assert report["report_status"] == "PASS"
    assert report["summary"]["matrix_rows"] == 30
    assert report["summary"]["gap_count"] == 0
    assert report["real_data_collected"] == 0
    assert all(row["coverage"]["status"] == "COMPLETE" for row in report["rows"])
