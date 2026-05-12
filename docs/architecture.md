# Architecture

AdaHarness is organized as a policy-driven modular harness system rather than a
full agent framework. Evaluation is a means to generate and validate policy, not
the final product boundary.

## Module Boundaries

- `adaharness/models/` defines model configuration, the `ModelClient` protocol,
  structured responses, and provider adapter boundaries.
- `adaharness/profiler/` produces a `ModelProfile` describing agent-relevant
  capability dimensions.
- `adaharness/policies/` maps a profile to a `HarnessPolicy`.
- `adaharness/specs/` will compile `HarnessPolicy` into runtime-facing
  `HarnessSpec` module configuration.
- `adaharness/modules/` will implement planner, verifier, retry, budget,
  context, tool, and trace modules.
- `adaharness/harnesses/` defines fixed presets and builds the adaptive harness.
- `adaharness/harnesses/runtime.py` defines executable runtime strategies for
  those presets without turning preset metadata into mutable execution state.
- `adaharness/evals/` loads task fixtures, estimates task success, and computes
  comparative metrics from run results.
- `adaharness/runtime/` contains state, budget, result, and tracing primitives.
- `adaharness/cli.py` wires the pipeline into `profile`, `recommend`, `compare`,
  and `report` commands.

## Current Runtime Shape

Version 0.1 intentionally uses synthetic profiling and deterministic evaluation
logic. This keeps the harness-selection loop testable before introducing real
model APIs, tool execution, or online policy updates.

The intended product data flow is:

```text
ModelProfile -> HarnessPolicy -> HarnessSpec -> ModularHarness -> RunTrace -> PolicyRefinement
```

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

The runtime data flow is:

```text
EvalTask + HarnessPolicy + ModelClient -> HarnessRuntime -> RunResult + RunTrace
```

Metrics are aggregates over `RunResult`, and reports should increasingly explain
their scores from `RunTrace` evidence rather than opaque estimates.
