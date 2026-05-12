# AdaHarness

Model-aware harness compiler for LLM agents.

AdaHarness profiles a model, generates a `HarnessPolicy`, and is being built to
assemble a modular harness that matches the model's capabilities, task type,
budget, and risk level.

When models change, the optimal harness often changes too. AdaHarness helps
detect harness drift, reduce overconstraint for stronger models, add control for
weaker models, and export executable harness specifications.

## Research Question

Most agent systems use a fixed harness across different models. AdaHarness
starts from a different assumption:

> When you change the model, you may need to change the harness.

A smaller model may need explicit planning, strict tool gating, retries, and
verification. A stronger model may perform better with fewer constraints, larger
autonomy windows, and selective verification.

## Core Ideas

- Model capability profiling
- `HarnessPolicy` generation
- `HarnessPolicy -> HarnessSpec` compilation
- Model migration and policy/module diff reporting
- Harness lift, harness tax, drift, and overconstraint measurement
- Runtime tracing for future policy refinement

## Current Status

Early experimental MVP.

The current version profiles a model, recommends a harness policy, compiles the
policy into a `HarnessSpec`, compares fixed and adaptive harnesses, records
traces, and emits JSON or Markdown reports.

## Install

```bash
uv sync --group dev
```

## Quick Start

```bash
uv run adaharness profile --model example-model
uv run adaharness recommend \
  --profile runs/example-model-profile.json \
  --risk medium \
  --budget standard \
  --out runs/example-model-policy.json
uv run adaharness assemble \
  --policy runs/example-model-policy.json \
  --out runs/example-model-harness-spec.json
uv run adaharness compare --model example-model --taskset tasks/eval --out runs/example-compare.json
uv run adaharness report runs/example-compare.json
```

You can also run the package without installing it:

```bash
uv run python -m adaharness.cli profile --model example-model
uv run python -m adaharness.cli compare --model example-model --taskset tasks/eval
```

Provider selection is available for the model-adapter boundary. The current
profiler remains deterministic until task-backed capability profiling is added.

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

See `docs/use-cases.md` for the target users, application scenarios, migration
workflow, and artifact model.

## Why

Agent performance is not only a property of the base model. It is shaped by the
surrounding harness: planning, tools, memory, retries, verification, context
management, and runtime policy.

AdaHarness treats the harness as something compiled from the model profile, not
hard-coded once.

## What AdaHarness Is Not

AdaHarness is not a replacement for LangChain, LangGraph, OpenAI Agents SDK, or
other agent runtimes. It is a runtime-agnostic harness policy and assembly layer
that can sit above different runtimes.

## MVP Scope

Version 0.1 focuses on harness selection, not open-ended harness generation.

- `bare`: minimal orchestration
- `light`: light planning and bounded retries
- `structured`: explicit planning, bounded retries, and selective verification
- `strong`: strict planning, strict tool gating, and always-on verification
- `adaptive`: selected from a model profile using a deterministic rule-based policy

Later versions can add LLM-generated policies, online policy changes, and richer
task domains.
