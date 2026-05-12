# Architecture

AdaHarness is organized as an embedded-first harness calibration and control
compiler rather than a full agent framework. It is the control plane that
decides how strongly an agent project should plan, verify, retry, tool-gate,
manage context, and budget autonomy. The user's agent runtime remains the data
plane that executes model calls, tools, state, streaming, and approvals.

The product flow is:

```text
ProjectAgentAdapter -> ProjectRunTrace -> AgentSystemProfile
  -> HarnessPolicy -> HarnessSpec -> RuntimeBinding -> project runtime hooks
```

The reference runtime flow is:

```text
ModelProfile -> HarnessPolicy -> HarnessSpec -> ModularHarness -> RunTrace
```

`ModularHarness` is a validation runtime for local experiments and CI. It is not
the expected production runtime for users who already have LangGraph, OpenAI
Agents SDK, Claude Agent SDK, or a custom agent loop.

## Package Boundaries

- `adaharness/models/` defines model configuration, the `ModelClient` protocol,
  structured responses, and provider adapter boundaries for lab runs.
- Future `adaharness/project/` owns project-local calibration interfaces:
  project adapters, project run results, and calibration artifacts.
- `adaharness/profiler/` produces a `ModelProfile` describing agent-relevant
  capability dimensions. Project calibration should later lift this into an
  `AgentSystemProfile`.
- `adaharness/policies/` maps a profile to `HarnessPolicy`, migration reports,
  and trace-backed refinements.
- `adaharness/specs/` compiles `HarnessPolicy` into runtime-neutral
  `HarnessSpec` controller plans.
- `adaharness/modules/` implements reference planner, verifier, retry, budget,
  context, tool, and trace behavior for local validation.
- `adaharness/harnesses/` contains preset harnesses and the reference
  `ModularHarness`.
- `adaharness/integrations/` normalizes external traces without executing
  external runtimes.
- `adaharness/evals/` loads task fixtures, estimates task success, and computes
  comparative metrics from run results.
- `adaharness/runtime/` contains state, budget, result, and tracing primitives.
- `adaharness/adapters/` binds controller specs to existing runtime hooks.
- `adaharness/cli.py` wires project-local calibration and lab commands.

## Current Runtime Shape

Current profiling remains deterministic and model-centric. Provider clients
exist, and `run` can call them through `ModelClient`, but project-local
calibration is still the main gap.

The provider boundary is separate:

```text
ModelConfig -> ModelClient -> ModelResponse
```

Provider-specific SDKs are optional dependencies and must stay behind
`adaharness.models`. Profilers and harness runtimes should depend on the
`ModelClient` protocol, not on OpenAI, Anthropic, or local HTTP clients directly.

Model support is protocol-first rather than brand-first. DeepSeek, Qwen, vLLM,
LM Studio, and similar endpoints should use the `openai-compatible` boundary
when they expose that protocol. Native provider adapters are reserved for real
protocol differences, not marketing names.

The reference runtime data flow is:

```text
EvalTask + HarnessPolicy + ModelClient -> HarnessRuntime -> RunResult + RunTrace
```

Metrics are aggregates over `RunResult`, and reports should explain their scores
from `RunTrace` evidence where possible.

Standalone reference runs are useful for AdaHarness development, examples, and
CI. User-facing policy value should come from a project adapter or imported
project traces, because the effective harness depends on the host runtime,
prompts, tools, task distribution, and failure modes.

See `docs/concepts/control-surface.md` for controller semantics and
`docs/concepts/policy-layer.md` for the control-plane boundary.
