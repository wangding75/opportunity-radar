from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from generate_functional_audit_report import build_report  # noqa: E402


def test_functional_audit_report_separates_static_evidence_from_readiness():
    report = build_report()
    assert report["report_status"] == "PASS"
    assert report["summary"]["matrix_rows"] == 30
    assert report["summary"]["gap_count"] == 0
    assert report["real_data_collected"] == 0
    assert report["summary"]["static_only_rows"] == 30
    assert all(row["coverage"]["status"] == "STATIC_ONLY" for row in report["rows"])
    assert report["validation_layers"]["runtime_functional_validation"]["status"] == "NOT_CHECKED"
    assert report["validation_layers"]["real_postgresql_validation"]["status"] == "RUNTIME_VERIFIED"
    assert report["validation_layers"]["external_integration_validation"]["status"] == "NOT_CHECKED"
    assert report["production_readiness"]["status"] == "NOT_READY"
    assert all(row["evidence_sources"] for row in report["rows"])
    assert report["summary"]["reverse_unregistered_count"] > 0
