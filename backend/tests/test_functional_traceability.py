from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_traceability import validate_traceability  # noqa: E402


def test_functional_traceability_maps_every_matrix_row_to_real_evidence():
    result = validate_traceability(
        Path(__file__).parents[2] / "validation" / "functional_matrix.json",
        Path(__file__).parents[2] / "validation" / "functional_traceability.json",
    )
    assert result["entries"] == result["matrix_rows"]
    assert result["entries"] >= 20
