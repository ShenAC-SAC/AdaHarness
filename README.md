# AdaHarness

Embedded-first harness calibration and control compiler for LLM agent projects.

AdaHarness evaluates an agent project, derives model/runtime capability signals,
generates a `HarnessPolicy`, and compiles a runtime-neutral control spec for how
much planning, verification, retry, tool control, context management, and
autonomy that project should use.

When models, tools, prompts, or tasks change, the optimal harness control surface
often changes too. AdaHarness helps detect harness drift, reduce overconstraint,
add control where needed, and export policy/spec/binding artifacts for the
project runtime.

## Research Question

Most agent systems use a fixed harness across changing models, prompts, tools,
and task distributions. AdaHarness starts from a different assumption:

> When the agent system changes, you may need to recalibrate harness controls.

A smaller model may need explicit planning, strict tool gating, retries, and
verification in one project, while the same model may need different controls in
another project with different tools, prompts, and failure modes.

## Core Ideas

- Project-local calibration from tasks and traces
- `HarnessPolicy` generation
- `HarnessPolicy -> HarnessSpec` control compilation
- `HarnessSpec -> RuntimeBinding` adapter reports
- Model migration and policy/controller diff reporting
- Harness lift, harness tax, drift, and overconstraint measurement
- Runtime tracing for future policy refinement

## Current Status

Early experimental MVP.

The current version has the policy, spec, controller, binding, config, reference
runtime, trace-import, and project calibration foundations. Project calibration
can run tasks through a host adapter and produce profile, policy, spec, binding,
runs, and report artifacts.

## Install

```bash
uv sync --group dev
```

## Embedded Usage

AdaHarness should usually be imported by an existing agent project. The project
keeps ownership of model providers, credentials, tools, prompts, and runtime
state.

```python
from adaharness import calibrate_agent_project
from adaharness.adapters import AdapterCapabilities

class MyAgentAdapter:
    name = "my-agent"

    def capabilities(self):
        return AdapterCapabilities(
            supports_pre_model_hook=True,
            supports_post_model_hook=True,
            supports_tool_interception=True,
            supports_retry_loop=True,
            supports_trace_export=True,
        )

    def run_task(self, task, *, binding=None):
        # Delegate to the host project's own model config, prompts, tools, and runtime.
        return my_agent_run_task(task, binding=binding)

result = calibrate_agent_project(
    MyAgentAdapter(),
    tasks=my_calibration_tasks,
    risk="medium",
    budget="standard",
)
binding = result.binding
```

For lower-level integrations, projects can still build artifacts directly:

```python
from adaharness import bind_harness_spec, compile_harness_spec, recommend_harness_policy

recommendation = recommend_harness_policy(project_profile)
spec = compile_harness_spec(recommendation, name="my-agent-controls")
binding = bind_harness_spec(
    spec,
    runtime="my-agent",
    capabilities=AdapterCapabilities(
        supports_pre_model_hook=True,
        supports_post_model_hook=True,
        supports_tool_interception=True,
        supports_retry_loop=True,
        supports_trace_export=True,
    ),
)
```

`binding` tells the host project which controllers map to which runtime hooks,
including levels, triggers, budgets, and escalation settings.

## Project-Local CLI

The CLI is not intended to be the production agent runner. It is a project-local
calibration, regression, trace-import, and artifact-generation tool. In a real
agent project, provider credentials should normally stay in that project.

For CLI experiments or CI, project configuration can live in `adaharness.toml`,
with secrets in `.env` only when AdaHarness itself owns the lab model call. For
embedded calibration, config should point to the host project's adapter:

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

See `docs/concepts/control-surface.md` for the controller model,
`docs/concepts/policy-layer.md` for the control-plane boundary, and
`docs/use-cases.md` for target users, migration workflows, and artifacts.

## Why

Agent performance is not only a property of the base model. It is shaped by the
surrounding harness: planning, tools, memory, retries, verification, context
management, and runtime policy.

AdaHarness treats harness control strength as something calibrated from the
agent project's model, runtime, task distribution, traces, risk, and budget, not
hard-coded once.

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
