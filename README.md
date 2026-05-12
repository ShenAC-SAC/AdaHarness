# AdaHarness

Adaptive harness selection and evaluation for LLM agents.

AdaHarness is an experimental framework for studying how different language
models require different agent harnesses. Smaller or less reliable models may
benefit from stronger workflow control, tool gating, retries, and verification.
Stronger models may perform better with lighter orchestration and fewer
constraints.

The goal is not to build one universal agent framework. The goal is to learn the
minimal effective harness for a given model, task, budget, and risk level.

## Core Ideas

- Model capability profiling
- Policy-based harness selection
- Bare vs light vs strong vs adaptive harness comparison
- Harness lift and harness tax measurement
- Runtime tracing for future harness evolution

## Current Status

Early experimental MVP.

The first version is intentionally evaluation-first: it profiles a model,
selects a harness preset, compares fixed and adaptive harnesses, and emits a
small JSON or Markdown report.

## Install

```bash
pip install -e .
```

## Quick Start

```bash
adaharness profile --model example-model
adaharness recommend --profile runs/example-model-profile.json
adaharness compare --model example-model --taskset tasks/eval --out runs/example-compare.json
adaharness report runs/example-compare.json
```

You can also run the package without installing it:

```bash
python -m adaharness.cli profile --model example-model
python -m adaharness.cli compare --model example-model --taskset tasks/eval
```

## Why

Agent performance is not only a property of the base model. It is shaped by the
surrounding harness: planning, tools, memory, retries, verification, context
management, and runtime policy.

AdaHarness explores how harnesses should adapt as models become more capable.

## MVP Scope

Version 0.1 focuses on harness selection, not open-ended harness generation.

- `bare`: minimal orchestration
- `light`: light planning and bounded retries
- `strong`: explicit planning, strict tool gating, and verification
- `adaptive`: selected from a model profile using a deterministic rule-based policy

Later versions can add LLM-generated policies, online policy changes, and richer
task domains.
