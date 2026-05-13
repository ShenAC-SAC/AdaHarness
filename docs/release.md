# Release Checklist

AdaHarness should be installable as a lightweight trace analyzer.

Install the current main branch with:

```bash
uv tool install git+https://github.com/ShenAC-SAC/AdaHarness.git
```

After a tagged PyPI release is published:

```bash
uv tool install adaharness
adaharness analyze \
  --traces examples/traces/overconstrained_harness.jsonl \
  --current-policy examples/policies/heavy_policy.json \
  --diagnostics-config examples/diagnostics/default.toml \
  --out runs/harness-drift.md
```

## Pre-Release Checks

Run locally before publishing:

```bash
uv run pytest -q
uv run ruff check .
uv run python -m compileall adaharness tests
uv lock --check
uv build
```

Verify the wheel contains the trace-first package surface:

```bash
python -m zipfile -l dist/adaharness-*.whl | rg "adaharness/(analysis|trace|api.py|cli.py)"
```

Smoke test the built wheel in a clean virtual environment:

```bash
python -m venv /tmp/adaharness-wheel-test
/tmp/adaharness-wheel-test/bin/pip install dist/adaharness-*.whl
cat > /tmp/adaharness-wheel-test/trace.jsonl <<'JSONL'
{"task_id":"t1","event":"verifier","status":"pass","cost":0.01}
{"task_id":"t1","event":"final","success":true,"cost":0.02}
JSONL
cat > /tmp/adaharness-wheel-test/policy.json <<'JSON'
{"verification_control":"always"}
JSON
/tmp/adaharness-wheel-test/bin/adaharness analyze \
  --traces /tmp/adaharness-wheel-test/trace.jsonl \
  --current-policy /tmp/adaharness-wheel-test/policy.json \
  --out /tmp/adaharness-wheel-test/harness-drift.md
```

## Publish

After configuring PyPI credentials or trusted publishing:

```bash
uv publish
```

Create a GitHub release with the same version tag and attach the generated
`dist/` artifacts if needed.
