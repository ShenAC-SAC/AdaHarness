# AdaHarness

Language: [English](README.md) | [简体中文](README.zh-CN.md)

Harness drift analyzer and calibration advisor for LLM agent projects.

AdaHarness reads agent traces and eval results, detects whether the current
harness is over-controlling or under-controlling the model, and suggests
evidence-backed policy changes.

When models, tools, prompts, or tasks change, the optimal harness control surface
often changes too. AdaHarness helps answer the first practical question:

> Did this change make our existing harness too heavy, too weak, or still
> appropriate?

## Research Question

Most agent systems keep the same planning, verification, retry, and tool-control
logic across changing models, prompts, tools, and task distributions. AdaHarness
starts from a different assumption:

> When the agent system changes, you may need to recalibrate harness controls.

A smaller model may need stricter control. A stronger model may be slowed down
by controls that no longer improve success. AdaHarness should make that drift
visible from traces before it tries to control any runtime.

## Core Ideas

- Trace ingestion from existing agent projects
- Harness metrics such as verifier catch rate, retry success rate, cost share,
  and latency overhead
- Overconstraint and underconstraint diagnosis
- Suggested policy diffs backed by trace evidence
- Model migration and harness drift reports
- Lightweight trace recorder SDK for host projects

## Current Status

Early experimental MVP.

The current codebase still contains earlier policy compiler, adapter, and
reference runtime foundations. Those are retained as experimental code. The MVP is
being reduced to a lighter loop:

```text
traces -> metrics -> diagnosis -> suggested policy diff -> report
```

## Install

From a release package:

```bash
uv tool install adaharness
# or: pipx install adaharness
```

For local development:

```bash
uv sync --group dev
```

After installation, you can create starter files:

```bash
adaharness init
```

This creates `.adaharness/diagnostics/default.toml`, `.adaharness/policies/current-policy.json`,
the built-in `agent-smoke` task suite, example traces, and a reports directory.
For real data, point `capture` at a single-task command that runs your agent:

```bash
adaharness capture \
  --out .adaharness/traces/run.jsonl \
  --analyze-out .adaharness/reports/harness-drift.md \
  --current-policy .adaharness/policies/current-policy.json \
  --diagnostics-config .adaharness/diagnostics/default.toml \
  -- python your_agent.py --prompt "{prompt}"
```

You can still run the bundled trace demo:

```bash
adaharness analyze \
  --traces .adaharness/traces/overconstrained_harness.jsonl \
  --current-policy .adaharness/policies/current-policy.json \
  --diagnostics-config .adaharness/diagnostics/default.toml \
  --out .adaharness/reports/harness-drift.md
```

## MVP Usage

The intended MVP flow is trace-first, but AdaHarness should help produce traces.
It does not assume your project has an `agent eval` command or a prepared test
set. The `capture` command ships with the `agent-smoke` suite and can run a
normal single-task agent entrypoint for each task, judge simple expectations,
and write AdaHarness traces.

The built-in suite is plain JSONL like this, so users can replace it later:

```json
{"task_id":"t1","prompt":"Answer with OK.","expected_contains":"OK"}
```

Capture command:

```bash
adaharness capture \
  --out .adaharness/traces/run.jsonl \
  -- python your_agent.py --prompt "{prompt}"
```

Use `--list-suites` to see bundled suites. Add `--tasks my-tasks.jsonl` only
when you want to replace the built-in suite with project-specific tasks.

If your agent prints lines prefixed with `ADAHARNESS_EVENT `, `capture` records
those as detailed harness events:

```text
ADAHARNESS_EVENT {"event":"tool_call","tool":"search_docs","status":"success","latency_ms":180}
```

For a bundled demo trace:

```bash
uv run adaharness analyze \
  --traces examples/traces/overconstrained_harness.jsonl \
  --current-policy examples/policies/heavy_policy.json \
  --diagnostics-config examples/diagnostics/default.toml \
  --out runs/harness-drift.md
```

Trace events can start small:

```json
{"task_id":"t1","event":"planner","latency_ms":320}
{"task_id":"t1","event":"verifier","status":"pass","cost":0.002}
{"task_id":"t1","event":"retry","reason":"tool_failure"}
{"task_id":"t1","event":"final","success":true,"cost":0.012,"latency_ms":2200}
```

AdaHarness should produce a report explaining whether controls are useful,
wasteful, or missing. That report is only meaningful for your project after you
replace the bundled demo trace with events from your own agent runs.

Diagnostic rules are configurable heuristics, not benchmark truth. Reports
include rule thresholds, observed values, evidence counts, confidence, and trace
quality warnings so recommendations stay auditable.

For the bundled example, the report should flag likely overconstraint: the
verifier rarely catches issues while adding cost, and explicit planning accounts
for a large latency share.

## How Projects Integrate

AdaHarness does not connect to your tools or execute your runtime. It only needs
your agent project to export trace events that describe what happened during
runs you already perform.

You can integrate in three ways:

- Write JSONL events directly from your project.
- Use `TraceRecorder` to write the same JSONL format.
- Convert existing logs or observability exports into AdaHarness trace events.

For example, a tool call in your project can become:

```json
{"task_id":"t1","event":"tool_call","tool":"search_docs","status":"success","latency_ms":180}
```

AdaHarness analyzes that event; it does not run `search_docs`.

Using the recorder:

```python
from adaharness.trace import TraceRecorder

trace = TraceRecorder(".adaharness/traces/run.jsonl", model="gpt-example", policy="current")
task = trace.task("support_001")

task.planner(latency_ms=320)
task.tool_call(tool="search_docs", status="success", latency_ms=180)
task.verifier(status="pass", cost=0.002)
task.final(success=True, cost=0.012, latency_ms=2200)
```

For timing a block without changing runtime behavior:

```python
with task.timed("tool_call", tool="search_docs"):
    search_docs(query)
```

The context manager records latency and failure status, then re-raises any
exception from the wrapped code.

Additional example traces are available:

```text
examples/traces/overconstrained_harness.jsonl
examples/traces/undercontrolled_tool_use.jsonl
examples/traces/balanced_harness.jsonl
examples/traces/migration_old_model.jsonl
examples/traces/migration_new_model.jsonl
```

## Project-Local CLI

The CLI is not intended to be the production agent runner. It is an analysis and
CI tool for traces exported by the user's existing agent project. Provider
credentials should normally stay in that project.

When `--out` is used, `analyze` writes a Markdown report plus structured
sidecars:

```text
runs/harness-drift.md
runs/harness-drift.analysis.json
runs/harness-drift.metrics.json
runs/harness-drift.diagnosis.json
runs/harness-drift.policy-diff.json
```

Older commands such as `profile`, `compare`, `recommend`, `assemble`,
`calibrate`, and reference `run` remain available for experiments and smoke
tests. They are not the main MVP path.

See `docs/metrics.md`, `docs/architecture.md`, `docs/roadmap.md`,
`docs/use-cases.md`, `docs/experimental.md`, and `docs/release.md` for the
current boundary and release checklist.

## Why

Agent performance is not only a property of the base model. It is shaped by the
surrounding harness: planning, tools, memory, retries, verification, context
management, and runtime policy.

AdaHarness treats harness control strength as something diagnosed from actual
runtime evidence, not inferred from abstract model scores alone.

## What AdaHarness Is Not

AdaHarness is not a replacement for LangChain, LangGraph, OpenAI Agents SDK, or
other agent runtimes. It should not require users to hand over runtime control
for the MVP. Runtime binding and adapter-based control are experimental.

## MVP Scope

Version 0.1 focuses on trace analysis:

- ingest JSONL traces
- record JSONL traces through the optional `TraceRecorder`
- compute harness metrics
- flag overconstraint and underconstraint signals
- recommend policy diffs
- render a Markdown report

Policy compilers, runtime bindings, project adapters, and the reference runtime
remain available as experimental scaffolding while the trace-first MVP proves
its value.
