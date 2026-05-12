# AdaHarness

Model-aware harness control compiler for LLM agents.

AdaHarness profiles a model, generates a `HarnessPolicy`, and compiles a
runtime-neutral control spec for how much planning, verification, retry, tool
control, context management, and autonomy an agent runtime should use.

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
- `HarnessPolicy -> HarnessSpec` control compilation
- Model migration and policy/controller diff reporting
- Harness lift, harness tax, drift, and overconstraint measurement
- Runtime tracing for future policy refinement

## Current Status

Early experimental MVP.

The current version profiles a model, recommends a harness policy, compiles the
policy into a `HarnessSpec`, runs tasks with a reference harness, compares fixed
and adaptive harnesses, records and imports traces, refines policies from trace
evidence, adapts active controls after retry signals, and emits policy diffs for
model migration.

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
uv run adaharness run \
  --harness-spec runs/example-model-harness-spec.json \
  --provider mock \
  --model mock-model \
  --task tasks/eval \
  --out runs/example-run.json
uv run adaharness compare --model example-model --taskset tasks/eval --out runs/example-compare.json
uv run adaharness report runs/example-compare.json
```

Project configuration can live in `adaharness.toml`, with secrets in `.env`:

```toml
[providers.deepseek]
type = "openai-compatible"
base_url = "https://api.deepseek.com/v1"
api_key_env = "DEEPSEEK_API_KEY"

[models.deepseek-chat]
provider = "deepseek"

[defaults]
risk = "medium"
budget = "standard"
taskset = "tasks/profiler"
```

```bash
uv run adaharness config validate --config adaharness.toml
uv run adaharness profile --config adaharness.toml --model deepseek-chat --out runs/profile.json
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

See `docs/concepts/control-surface.md` for the controller model,
`docs/concepts/policy-layer.md` for the control-plane boundary, and
`docs/use-cases.md` for target users, migration workflows, and artifacts.

## Why

Agent performance is not only a property of the base model. It is shaped by the
surrounding harness: planning, tools, memory, retries, verification, context
management, and runtime policy.

AdaHarness treats harness control strength as something compiled from the model
profile, task, risk, and budget, not hard-coded once.

## What AdaHarness Is Not

AdaHarness is not a replacement for LangChain, LangGraph, OpenAI Agents SDK, or
other agent runtimes. It is a runtime-agnostic harness policy and control layer
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
