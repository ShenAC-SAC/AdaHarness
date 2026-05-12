# AdaHarness

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
- Lightweight trace recorder SDK in future versions

## Current Status

Early experimental MVP.

The current codebase still contains earlier policy compiler, adapter, and
reference runtime foundations. Those are now considered experimental. The MVP is
being reduced to a lighter loop:

```text
traces -> metrics -> diagnosis -> suggested policy diff -> report
```

## Install

```bash
uv sync --group dev
```

## MVP Usage

The intended MVP flow is trace-first. A project exports JSONL traces or eval
results, then AdaHarness analyzes harness drift:

```bash
uv run adaharness analyze \
  --traces examples/traces/overconstrained_harness.jsonl \
  --current-policy examples/policies/heavy_policy.json \
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
wasteful, or missing.

For the bundled example, the report should flag likely overconstraint: the
verifier rarely catches issues while adding cost, and explicit planning accounts
for a large latency share.

## Project-Local CLI

The CLI is not intended to be the production agent runner. It is an analysis and
CI tool for traces exported by the user's existing agent project. Provider
credentials should normally stay in that project.

The previous project adapter flow remains experimental:

```toml
[project]
name = "my-agent"
adapter = "my_agent.adaharness_adapter:MyAgentAdapter"
taskset = "tests/adaharness_tasks"
artifact_dir = ".adaharness"

[defaults]
risk = "medium"
budget = "standard"
```

```bash
uv run adaharness config validate --config adaharness.toml
uv run adaharness calibrate --config adaharness.toml
```

The current CLI also includes lab commands backed by AdaHarness' reference
runtime. They are useful for smoke tests and examples, not as the main product
flow:

```bash
uv run python -m adaharness.cli profile --model example-model
uv run python -m adaharness.cli compare --model example-model --taskset tasks/eval
```

Provider selection is available for the model-adapter boundary. The current
profiler remains deterministic and is mainly a lab path.

```bash
uv run adaharness profile --provider mock --model mock-model
uv run adaharness compare --provider openai-compatible --model gpt-5.5 --taskset tasks/eval
uv run adaharness compare --provider openai-compatible --model deepseek-chat --base-url <provider-url> --taskset tasks/eval
uv run adaharness compare --provider openai-compatible --model qwen --base-url <provider-url> --taskset tasks/eval
```

Compare multiple model profiles against multiple harnesses:

```bash
uv run adaharness compare \
  --models small-sim,strong-sim \
  --harnesses bare,light,structured,strong,adaptive \
  --taskset tasks/eval \
  --out runs/model-harness-matrix.json

uv run adaharness report runs/model-harness-matrix.json
```

Optional provider dependencies can be installed when needed:

```bash
uv sync --group dev --extra openai
uv sync --group dev --extra anthropic
uv sync --group dev --extra local
```

See `docs/models.md` for the model support strategy. In short, OpenAI and
Anthropic are useful strong-model baselines, but AdaHarness is especially aimed
at comparing harness choices for open, local, and OpenAI-compatible models where
the right orchestration layer may have a larger effect.

See `docs/architecture.md`, `docs/roadmap.md`, and `docs/use-cases.md` for the
current trace-first MVP boundary.

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
- compute harness metrics
- flag overconstraint and underconstraint signals
- recommend policy diffs
- render a Markdown report

Policy compilers, runtime bindings, project adapters, and the reference runtime
remain available as experimental scaffolding while the trace-first MVP proves
its value.
