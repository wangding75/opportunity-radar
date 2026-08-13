from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_dependency_supply_chain_review import validate_dependency_review  # noqa: E402


def test_dependency_supply_chain_review_is_pinned_and_complete():
    result = validate_dependency_review(Path(__file__).parents[2] / "validation" / "security_review_dependency_supply_chain.json")
    assert result["controls"] == 6
    assert result["production_lock"] >= 10
    assert result["development_lock"] >= result["production_lock"]
    assert result["sbom_components"] >= result["production_lock"]
    assert result["status"] == "PASS"
