# False-completion regression gate

`scripts/validate_false_completion_gate.py` is the continuous regression gate
for the T117 review. It reruns and cross-checks:

1. the code/test false-completion scanner;
2. the itemized remediation ledger;
3. feature-to-code/API/UI/Worker/test traceability;
4. the functional zero-gap scanner;
5. the generated functional audit report; and
6. the SYNTHETIC/MOCK-only data policy with zero live data collected.

The gate emits `validation/false_completion_gate.json` and fails if any check
is false. Product validation invokes the same command, and the regression test
executes it as a normal test path:

```text
python scripts/validate_false_completion_gate.py
```

This is a repository-local gate. It does not contact external providers.
