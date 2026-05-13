# Release Checklist

AdaHarness is designed to be usable after package installation:

```bash
uv tool install adaharness
adaharness init
adaharness analyze \
  --traces .adaharness/traces/overconstrained_harness.jsonl \
  --current-policy .adaharness/policies/current-policy.json \
  --diagnostics-config .adaharness/diagnostics/default.toml \
  --out .adaharness/reports/harness-drift.md
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

Verify the wheel contains starter templates:

```bash
python -m zipfile -l dist/adaharness-*.whl | rg "adaharness/templates"
```

Smoke test the built wheel in a clean virtual environment:

```bash
python -m venv /tmp/adaharness-wheel-test
/tmp/adaharness-wheel-test/bin/pip install dist/adaharness-*.whl
/tmp/adaharness-wheel-test/bin/adaharness init --path /tmp/adaharness-wheel-test/project/.adaharness
/tmp/adaharness-wheel-test/bin/adaharness capture \
  --tasks /tmp/adaharness-wheel-test/project/.adaharness/tasks/sample-tasks.jsonl \
  --out /tmp/adaharness-wheel-test/project/.adaharness/traces/run.jsonl \
  -- python -c 'import sys; print("OK")'
/tmp/adaharness-wheel-test/bin/adaharness analyze \
  --traces /tmp/adaharness-wheel-test/project/.adaharness/traces/run.jsonl \
  --current-policy /tmp/adaharness-wheel-test/project/.adaharness/policies/current-policy.json \
  --diagnostics-config /tmp/adaharness-wheel-test/project/.adaharness/diagnostics/default.toml \
  --out /tmp/adaharness-wheel-test/project/.adaharness/reports/harness-drift.md
```

## Publish

After configuring PyPI credentials or trusted publishing:

```bash
uv publish
```

Create a GitHub release with the same version tag and attach the generated
`dist/` artifacts if needed.
