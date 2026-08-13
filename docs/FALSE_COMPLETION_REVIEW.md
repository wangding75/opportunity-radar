# False-completion review

`validation/false_completion_rules.json` and
`scripts/validate_false_completion.py` define the repository's false-completion
rules. The scanner covers Python/TypeScript implementation and test roots and
fails on:

- `TODO` or `FIXME` markers;
- skipped or trivial tests (`pytest.mark.skip`, `pytest.skip`, `unittest.skip`,
  and `assert True`);
- empty function/class bodies;
- product API handlers returning an empty literal; and
- unapproved `NotImplementedError` extension points.

Abstract connector/analyzer contracts, provider payload hooks and typed
provider-routing exception classes are explicit allowlist entries with reasons.
They are reported as exceptions rather than silently ignored. Empty data
results inside real business branches remain valid and are not rejected by a
naive `return []`/`return None` search.

Run the scan with:

```text
python scripts/validate_false_completion.py
```

The deterministic result is written to
`validation/false_completion_scan.json`; product validation and regression
tests require zero unapproved violations. Validation uses only repository code
and existing SYNTHETIC/MOCK tests.
