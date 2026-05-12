# AdaHarness

Adaptive harness selection and evaluation for LLM agents.

AdaHarness is an experimental framework for studying how different language
models require different agent harnesses. Smaller or less reliable models may
benefit from stronger workflow control, tool gating, retries, and verification.
Stronger models may perform better with lighter orchestration and fewer
constraints.

The goal is not to build one universal agent framework. The goal is to learn the
minimal effective harness for a given model, task, budget, and risk level.

## Research Question

Most agent frameworks apply the same orchestration pattern to every model.
AdaHarness starts from a different assumption:

> Different models need different levels of harness control.

A smaller model may need explicit planning, strict tool gating, retries, and
verification. A stronger model may perform better with fewer constraints, larger
autonomy windows, and selective verification.

## Core Ideas

- Model capability profiling
- Policy-based harness selection
- Bare vs light vs structured vs strong vs adaptive harness comparison
- Harness lift and harness tax measurement
- Runtime tracing for future harness evolution

## Current Status

Early experimental MVP.

The first version is intentionally evaluation-first: it profiles a model,
selects a harness preset, compares fixed and adaptive harnesses, and emits a
small JSON or Markdown report.

## Install

```bash
uv sync --group dev
```

## Quick Start

```bash
uv run adaharness profile --model example-model
uv run adaharness recommend --profile runs/example-model-profile.json
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

## Why

Agent performance is not only a property of the base model. It is shaped by the
surrounding harness: planning, tools, memory, retries, verification, context
management, and runtime policy.

AdaHarness explores how harnesses should adapt as models become more capable.

## What AdaHarness Is Not

AdaHarness is not a replacement for LangChain, LangGraph, OpenAI Agents SDK, or
other agent runtimes. It is an evaluation-first adaptive harness layer that can
sit above different runtimes.

## MVP Scope

Version 0.1 focuses on harness selection, not open-ended harness generation.

- `bare`: minimal orchestration
- `light`: light planning and bounded retries
- `structured`: explicit planning, bounded retries, and selective verification
- `strong`: strict planning, strict tool gating, and always-on verification
- `adaptive`: selected from a model profile using a deterministic rule-based policy

Later versions can add LLM-generated policies, online policy changes, and richer
task domains.
