from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_functional_matrix import validate_matrix  # noqa: E402


def test_functional_matrix_has_complete_safe_traceability():
    result = validate_matrix(Path(__file__).parents[2] / "validation" / "functional_matrix.json")
    assert result["rows"] >= 20
    assert {"Observation", "Keyword", "Trend", "Graph", "Opportunity", "Alert", "Delivery", "Enterprise", "Security", "Operations"} <= set(result["areas"])
