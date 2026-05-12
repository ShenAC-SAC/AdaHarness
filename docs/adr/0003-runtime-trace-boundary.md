# ADR 0003: Separate Harness Presets from Runtime Execution

## Status

Accepted

## Context

AdaHarness already has `Harness` objects that represent named policy presets.
Those objects are useful for policy selection and synthetic scoring, but making
them responsible for execution would mix configuration, runtime state, model
calls, and trace capture.

## Decision

Keep `Harness` as immutable preset metadata. Add a separate `HarnessRuntime`
protocol that runs an `EvalTask` through a `ModelClient` with a selected
`HarnessPolicy`, `Budget`, and provider-neutral `RunTrace`.

Evaluation owns scoring and attaches final outcomes to `RunResult`. Runtime
owns control-flow evidence such as planning, LLM calls, verification, context
management, and future retry/policy-change events.

## Consequences

- Policy presets remain cheap and easy to compare.
- Runtime implementations can evolve without rewriting policy generation.
- Trace-backed reporting can be added incrementally.
- Synthetic estimates remain compatible while executable runtimes mature.
