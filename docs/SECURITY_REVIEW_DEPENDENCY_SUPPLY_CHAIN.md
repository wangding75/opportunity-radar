# Dependency and supply-chain security review

`validation/security_review_dependency_supply_chain.json` records six PASS
controls covering the production and development Python locks, frontend
package lock, CycloneDX SBOM fingerprint, Docker build context/runtime image,
and product-gate integration. The validator independently checks exact pins,
the TypeScript lock, SBOM purls and the fingerprint derived from the SBOM set.

Run the review:

```text
python scripts/validate_dependency_supply_chain_review.py
```

The normal product validation still runs `scripts/validate_supply_chain.py`,
which additionally checks installed development package versions and the
checked-in SBOM release metadata. No external vulnerability feed or live data
is contacted by this review.
