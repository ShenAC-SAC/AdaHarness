# Architecture

AdaHarness is organized as a lightweight evaluation pipeline rather than a full
agent framework.

## Module Boundaries

- `adaharness/models/` defines model configuration and future provider adapter
  boundaries.
- `adaharness/profiler/` produces a `ModelProfile` describing agent-relevant
  capability dimensions.
- `adaharness/policies/` maps a profile to a `HarnessPolicy`.
- `adaharness/harnesses/` defines fixed presets and builds the adaptive harness.
- `adaharness/evals/` loads task fixtures, estimates task success, and computes
  comparative metrics.
- `adaharness/runtime/` contains early state, budget, and tracing primitives.
- `adaharness/cli.py` wires the pipeline into `profile`, `recommend`, `compare`,
  and `report` commands.

## Current Runtime Shape

Version 0.1 intentionally uses synthetic profiling and deterministic evaluation
logic. This keeps the harness-selection loop testable before introducing real
model APIs, tool execution, or online policy updates.

The main data flow is:

```text
model name -> ModelProfile -> HarnessPolicy -> Harness -> HarnessMetrics -> report
```

Future versions should keep provider-specific code behind model adapters and
avoid mixing model calls directly into policy generation or metric calculation.
