# AdaHarness

Language: [English](README.md) | [简体中文](README.zh-CN.md)

AdaHarness is a lightweight trace analyzer for agent developers. It helps you
recalibrate harness controls after changing the underlying LLM, prompt, tools,
or task distribution.

The core question is:

> After this change, is our existing planning, verification, retry, and tool
> control layer still appropriate, too heavy, or too weak?

AdaHarness does not run your agent, wrap your tools, manage model credentials,
or control your runtime. You run your own evals normally, export JSONL traces,
and let AdaHarness analyze the evidence.

## MVP Flow

```text
exported traces -> validation -> metrics -> diagnosis -> policy diff -> report
```

AdaHarness produces:

- a fit verdict such as `well_fit`, `likely_overcontrolled`,
  `likely_undercontrolled`, `mixed_signals`, or `insufficient_evidence`
- trace quality warnings
- harness metrics such as verifier catch rate, retry success rate, verifier cost
  share, planner latency share, and tool failure rate
- overconstraint and underconstraint diagnostics
- evidence-backed policy diff recommendations
- a Markdown report plus structured JSON sidecars

## Install

From a checkout:

```bash
uv sync --group dev
uv run adaharness --help
```

From GitHub:

```bash
uv tool install git+https://github.com/ShenAC-SAC/AdaHarness.git
```

## Quick Start

From a source checkout, run the bundled trace example:

```bash
uv run adaharness analyze \
  --traces examples/traces/overconstrained_harness.jsonl \
  --current-policy examples/policies/heavy_policy.json \
  --diagnostics-config examples/diagnostics/default.toml \
  --out runs/harness-drift.md
```

This writes:

```text
runs/harness-drift.md
runs/harness-drift.analysis.json
runs/harness-drift.metrics.json
runs/harness-drift.diagnosis.json
runs/harness-drift.policy-diff.json
```

## Trace Format

The trace contract is intentionally small. Each JSONL line is one event. The
required fields are `task_id` and `event`.

```json
{"task_id":"t1","event":"planner","latency_ms":320}
{"task_id":"t1","event":"verifier","status":"pass","cost":0.002}
{"task_id":"t1","event":"retry","reason":"tool_failure"}
{"task_id":"t1","event":"final","success":true,"cost":0.012,"latency_ms":2200}
```

Useful optional fields include `status`, `success`, `cost`, `latency_ms`,
`tokens`, `model`, `policy`, `task_type`, `control`, and `reason`.

Canonical event names include:

- `planner`
- `verifier`
- `retry`
- `tool_call`
- `tool_result_ignored`
- `model_call`
- `context`
- `subagent`
- `final`

Unknown events are reported as validation warnings rather than hard failures, so
host projects can start small and enrich traces over time.

## Integration Options

You can integrate in three lightweight ways:

- Write AdaHarness-compatible JSONL directly from your project.
- Use the optional `TraceRecorder` helper.
- Convert existing logs or observability exports into AdaHarness JSONL before
  running `analyze`.

Using the recorder:

```python
from adaharness.trace import TraceRecorder

trace = TraceRecorder("traces/run.jsonl", model="gpt-example", policy="current")
task = trace.task("support_001")

task.planner(latency_ms=320)
task.tool_call(tool="search_docs", status="success", latency_ms=180)
task.verifier(status="pass", cost=0.002)
task.final(success=True, cost=0.012, latency_ms=2200)
```

Timing a block:

```python
with task.timed("tool_call", tool="search_docs"):
    search_docs(query)
```

The context manager records latency and failure status, then re-raises any
exception from the wrapped code. It does not mutate the host runtime.

## Policy Diff

`--current-policy` is optional. When present, it should be a simple JSON object
describing current control settings:

```json
{
  "planning_control": "explicit",
  "verification_control": "always",
  "retry_control": "bounded",
  "tool_control": "moderate"
}
```

AdaHarness may recommend changes such as:

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

Recommendations are advisory. AdaHarness does not apply them to your project.
For a single trace set, the fit verdict is observational: it summarizes current
evidence, but it does not prove that a policy is optimal without a baseline or
policy comparison run.

When one trace file contains multiple models, policies, or task types, group the
analysis explicitly:

```bash
adaharness analyze \
  --traces traces/mixed.jsonl \
  --group-by model,policy \
  --out reports/harness-fit.md
```

Without grouping, AdaHarness warns when aggregate metrics may mix different
model or harness contexts.

## Python API

```python
from adaharness import analyze_traces

result = analyze_traces(
    ["traces/run.jsonl"],
    current_policy={"verification_control": "always"},
)

print(result["report"])
print(result["policy_diff"])
```

## Project Scope

AdaHarness is not a replacement for LangChain, LangGraph, OpenAI Agents SDK, or
other agent runtimes. It is not a model provider wrapper, policy compiler,
reference harness, or project adapter system.

The maintained MVP surface is:

- `adaharness/analysis/`
- `adaharness/trace/`
- `adaharness/api.py`
- `adaharness/cli.py`

## Development

```bash
uv sync --group dev
uv run pytest -q
uv run ruff check .
uv run python -m compileall adaharness tests
```
