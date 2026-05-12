# Architecture

AdaHarness is organized as a harness policy/compiler layer rather than a full
agent framework. It is the control plane that decides which harness controls a
model should receive. The user's agent runtime remains the data plane that
executes model calls, tools, state, streaming, and approvals.

The product flow is:

```text
ModelProfile -> HarnessPolicy -> HarnessSpec -> RuntimeBinding -> external runtime
```

The reference runtime flow is:

```text
ModelProfile -> HarnessPolicy -> HarnessSpec -> ModularHarness -> RunTrace
```

`ModularHarness` is a validation runtime for local experiments and CI. It is not
the expected production runtime for users who already have LangGraph, OpenAI
Agents SDK, Claude Agent SDK, or a custom agent loop.

## Module Boundaries

- `adaharness/models/` defines model configuration, the `ModelClient` protocol,
  structured responses, and provider adapter boundaries.
- `adaharness/profiler/` produces a `ModelProfile` describing agent-relevant
  capability dimensions.
- `adaharness/policies/` maps a profile to `HarnessPolicy`, migration reports,
  and trace-backed refinements.
- `adaharness/specs/` compiles `HarnessPolicy` into runtime-neutral
  `HarnessSpec` controls.
- `adaharness/modules/` implements reference planner, verifier, retry, budget,
  context, tool, and trace controls.
- `adaharness/harnesses/` contains preset harnesses and the reference
  `ModularHarness`.
- `adaharness/integrations/` normalizes external traces without executing
  external runtimes.
- `adaharness/evals/` loads task fixtures, estimates task success, and computes
  comparative metrics from run results.
- `adaharness/runtime/` contains state, budget, result, and tracing primitives.
- Future `adaharness/adapters/` will bind specs to existing runtimes.
- `adaharness/cli.py` wires the standalone lab commands.

## Current Runtime Shape

Current profiling remains deterministic. Provider clients exist, and `run` can
call them through `ModelClient`, but live profiling is still a gap.

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

See `docs/concepts/policy-layer.md` for the control-plane boundary.
