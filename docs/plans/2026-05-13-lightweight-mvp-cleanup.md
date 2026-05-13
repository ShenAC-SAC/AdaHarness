# Lightweight MVP Cleanup Implementation Plan

> **Implementation note:** Execute this cleanup task-by-task and verify after each boundary change.

**Goal:** Reduce AdaHarness to a lightweight trace-first harness calibration tool that recommends policy diffs after an agent project's underlying LLM changes.

**Architecture:** The retained product path is `exported traces -> validation -> metrics -> diagnosis -> policy diff -> report`. AdaHarness must not run, wrap, adapt, or control the user's agent runtime in the MVP. Users either write AdaHarness-compatible JSONL directly or use the optional `TraceRecorder` SDK.

**Tech Stack:** Python 3.10+, stdlib JSON/JSONL/TOML handling, argparse CLI, pytest/unittest tests, Ruff linting.

---

## Product Boundary

### Target User

Agent developers who already have an agent project and want to recalibrate harness controls after changing the base LLM, prompt, tools, or task distribution.

### Core Question

After a model migration, is the existing harness layer still appropriate, too heavy, or too weak?

### MVP Output

The MVP should output structured, evidence-backed policy diffs rather than trying to apply changes automatically. A recommendation should say which control to change, from what value to what value, why, and which trace evidence supports it.

Examples:

```json
{
  "field": "verification_control",
  "from": "always",
  "to": "selective",
  "reason": "Verifier appears expensive but rarely catches failures.",
  "evidence": ["verifier_catch_rate=0.00", "verifier_cost_share=0.25"],
  "confidence": "medium",
  "evidence_count": 20
}
```

### Main User Flow

```text
User runs their own agent/eval normally
-> user exports AdaHarness JSONL traces
-> adaharness analyze --traces run.jsonl --current-policy policy.json --out report.md
-> AdaHarness writes report.md and JSON sidecars
```

### Non-Goals

- Do not run user agent commands as the primary workflow.
- Do not provide a reference agent runtime.
- Do not require project adapters.
- Do not compile policies into executable runtime specs.
- Do not manage model provider credentials.
- Do not auto-apply policy changes to user projects.
- Do not keep built-in workload suites as the main integration story.

## Keep

These pieces are part of the lightweight MVP:

- `adaharness/analysis/`
  - trace ingestion
  - trace validation
  - metrics
  - diagnostics
  - policy diff recommendation
  - Markdown report rendering
- `adaharness/trace/`
  - optional `TraceRecorder`
  - JSONL writer only
  - no runtime control or hooks
- `adaharness/cli.py`
  - keep only `analyze` as the stable command
  - optionally keep a minimal help path
- `examples/traces/`
  - small canonical demo traces
- `examples/policies/`
  - simple current policy JSON examples
- `examples/diagnostics/`
  - optional diagnostic threshold config
- Tests for analysis, trace recorder, and the analyze CLI.

## Remove

These pieces are outside the new MVP and should be deleted rather than kept as experimental scaffolding:

- `adaharness/adapters/`
- `adaharness/evals/`
- `adaharness/harnesses/`
- `adaharness/integrations/`
- `adaharness/models/`
- `adaharness/modules/`
- `adaharness/policies/`
- `adaharness/profiler/`
- `adaharness/project/`
- `adaharness/runtime/`
- `adaharness/specs/`
- `adaharness/capture.py`
- `adaharness/config.py`
- heavy public API functions in `adaharness/api.py`
- CLI commands:
  - `init`
  - `capture`
  - `calibrate`
  - `profile`
  - `recommend`
  - `assemble`
  - `compare`
  - `run`
  - `migrate`
  - `refine`
  - `import-trace`
  - `config`
  - `report`
- tests that only cover removed runtime/control/profiler/adapters/specs/model behavior
- `tasks/`
- `adaharness/templates/`
- runtime-control examples such as `examples/compare_harnesses.py` and `examples/run_openai_compatible.py`
- generated sample outputs in `runs/` if they are tracked

## Rebuild the Public API

Replace `adaharness/api.py` with a trace-first API:

```python
from pathlib import Path
from typing import Any

from adaharness.analysis import (
    compute_trace_metrics,
    diagnose_harness,
    load_diagnostic_config,
    load_trace_events,
    recommend_policy_changes,
    render_analysis_report,
    validate_trace_events,
)


def analyze_traces(
    traces: list[str | Path],
    *,
    current_policy: dict[str, Any] | None = None,
    diagnostics_config: str | Path | None = None,
) -> dict[str, Any]:
    ...
```

The function should return a structured dict with:

- `diagnostics_config`
- `metrics`
- `trace_warnings`
- `diagnosis`
- `policy_diff`
- `report`

`adaharness/__init__.py` should export only:

- `__version__`
- `TraceRecorder`
- `TraceEvent`
- `analyze_traces`
- core analysis dataclasses and functions if useful

## CLI Shape

`adaharness --help` should make the tool feel small:

```text
usage: adaharness [-h] {analyze} ...
```

`adaharness analyze` remains:

```bash
adaharness analyze \
  --traces examples/traces/overconstrained_harness.jsonl \
  --current-policy examples/policies/heavy_policy.json \
  --diagnostics-config examples/diagnostics/default.toml \
  --out runs/harness-drift.md
```

Sidecars remain:

```text
runs/harness-drift.analysis.json
runs/harness-drift.metrics.json
runs/harness-drift.diagnosis.json
runs/harness-drift.policy-diff.json
```

## Trace Contract

Keep the trace contract intentionally small. Required fields:

- `task_id`
- `event`

Important optional fields:

- `status`
- `success`
- `cost`
- `latency_ms`
- `tokens`
- `model`
- `policy`
- `control`
- `reason`

Canonical events:

- `planner`
- `verifier`
- `retry`
- `tool_call`
- `tool_result_ignored`
- `model_call`
- `context`
- `subagent`
- `final`

Unknown events should produce validation warnings, not hard failures, unless required fields are missing.

## Documentation Positioning

Rewrite the README around one sentence:

> AdaHarness is a lightweight trace analyzer that helps agent developers recalibrate harness controls after changing the underlying LLM.

The README should show three integration options:

1. Write JSONL events directly.
2. Use `TraceRecorder`.
3. Convert existing logs externally, then pass JSONL to `analyze`.

Remove primary docs that imply AdaHarness is a runtime, model profiler, harness builder, policy compiler, or agent runner.

Add or update an ADR:

- supersede ADR 0008
- state that runtime scaffolding is being removed, not merely hidden
- record the reason: keeping it creates user confusion and maintenance drag before the trace analyzer has proved product value

## Implementation Tasks

### Task 1: Freeze the New Boundary in Docs

**Files:**

- Create: `docs/adr/0009-remove-runtime-scaffolding.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/architecture.md`
- Modify: `docs/roadmap.md`

**Step 1:** Add ADR 0009 stating that ADR 0008 is superseded.

**Step 2:** Rewrite the README quick start around trace export and `analyze`.

**Step 3:** Remove `capture`, adapter, runtime, model profiler, and policy compiler from the main docs.

**Step 4:** Run:

```bash
uv run python -m compileall adaharness tests
```

Expected: no syntax errors.

### Task 2: Shrink the CLI to Analyze

**Files:**

- Modify: `adaharness/cli.py`
- Modify: `tests/test_cli_analyze.py`
- Delete: `tests/test_cli_capture.py`
- Delete: `tests/test_cli_calibrate.py`
- Delete: `tests/test_cli_init.py`
- Delete or rewrite: `tests/test_cli.py`

**Step 1:** Remove imports that reference removed modules.

**Step 2:** Keep `_load_policy_dict`, `_write_json`, `_write_analysis_sidecars`, `_run_analysis`, `cmd_analyze`, `build_parser`, and `main`.

**Step 3:** Ensure `build_parser()` registers only `analyze`.

**Step 4:** Add a CLI test that `--help` exposes only `analyze`.

**Step 5:** Run:

```bash
uv run pytest -q tests/test_cli_analyze.py
```

Expected: pass.

### Task 3: Replace the Public API

**Files:**

- Modify: `adaharness/api.py`
- Modify: `adaharness/__init__.py`
- Modify or create: `tests/test_api.py`

**Step 1:** Delete runtime/profile/policy-compiler API exports.

**Step 2:** Add `analyze_traces(...)`.

**Step 3:** Export `TraceRecorder` from the top-level package.

**Step 4:** Test that `analyze_traces` returns metrics, diagnosis, policy diff, and report for a small trace file.

**Step 5:** Run:

```bash
uv run pytest -q tests/test_api.py tests/test_trace_recorder.py tests/test_analysis.py
```

Expected: pass.

### Task 4: Delete Runtime-Control Packages

**Files:**

- Delete: `adaharness/adapters/`
- Delete: `adaharness/evals/`
- Delete: `adaharness/harnesses/`
- Delete: `adaharness/integrations/`
- Delete: `adaharness/models/`
- Delete: `adaharness/modules/`
- Delete: `adaharness/policies/`
- Delete: `adaharness/profiler/`
- Delete: `adaharness/project/`
- Delete: `adaharness/runtime/`
- Delete: `adaharness/specs/`
- Delete: `adaharness/capture.py`
- Delete: `adaharness/config.py`

**Step 1:** Delete one package group at a time.

**Step 2:** Run import checks after each group:

```bash
uv run python -m compileall adaharness tests
```

Expected: no imports refer to deleted packages.

**Step 3:** Use `rg` to confirm:

```bash
rg "adaharness\\.(adapters|evals|harnesses|integrations|models|modules|policies|profiler|project|runtime|specs|capture|config)"
```

Expected: no remaining matches outside historical ADR text, if that text is intentionally retained.

### Task 5: Delete Non-MVP Tests and Fixtures

**Files:**

- Delete tests for removed packages.
- Keep:
  - `tests/test_analysis.py`
  - `tests/test_cli_analyze.py`
  - `tests/test_trace_recorder.py`
  - focused API tests after rewrite

**Step 1:** Remove tests that reference deleted packages.

**Step 2:** Run:

```bash
uv run pytest -q
```

Expected: all remaining tests pass.

### Task 6: Clean Examples, Templates, Tasks, and Runs

**Files:**

- Delete: `adaharness/templates/`
- Delete: `tasks/`
- Delete: runtime-control example scripts.
- Keep:
  - `examples/traces/*.jsonl`
  - `examples/policies/heavy_policy.json`
  - `examples/diagnostics/default.toml`

**Step 1:** Remove examples that require AdaHarness to run models or compare harness presets.

**Step 2:** Remove committed generated outputs under `runs/`, unless they are intentionally kept as golden fixtures.

**Step 3:** Add or verify `.gitignore` ignores `runs/`, `dist/`, `.venv/`, `.pytest_cache/`, `.ruff_cache/`, and `.uv-cache/`.

### Task 7: Final Verification

Run:

```bash
uv run ruff check .
uv run pytest -q
uv run python -m compileall adaharness tests
uv run adaharness analyze \
  --traces examples/traces/overconstrained_harness.jsonl \
  --current-policy examples/policies/heavy_policy.json \
  --diagnostics-config examples/diagnostics/default.toml \
  --out runs/harness-drift.md
```

Expected:

- Ruff passes.
- Tests pass.
- Compileall passes.
- Analyze writes report and sidecars.

## Open Decisions Before Deletion

These are the only decisions worth confirming before code removal:

1. Whether `import-trace` should be reimplemented later as a pure JSON normalizer, separate from the removed runtime trace model.
2. Whether `init` should be removed entirely or replaced later by a tiny `trace schema` example generator.
3. Whether historical ADRs should stay for project history or be pruned from public-facing docs.

The default for this cleanup should be deletion. Reintroduction should require a direct user-facing need in the trace-first workflow.
