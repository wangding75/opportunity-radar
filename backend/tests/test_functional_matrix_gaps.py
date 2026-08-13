from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from scan_functional_matrix_gaps import scan_gaps  # noqa: E402


def test_functional_matrix_gap_scan_has_no_unexplained_chain_gaps():
    result = scan_gaps()
    assert result["gap_count"] == 0
    assert result["matrix_rows"] == result["traceability_entries"]
