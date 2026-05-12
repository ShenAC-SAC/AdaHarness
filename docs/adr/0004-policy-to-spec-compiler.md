# ADR 0004: Introduce HarnessSpec Between Policy and Runtime

## Status

Accepted

## Context

`HarnessPolicy` is the right shape for rule systems, LLM proposals, and users:
it says how much planning, verification, retry, gatekeeping, context management,
and autonomy should be used. Runtime modules need a more concrete configuration:
which modules are enabled, what parameters they receive, and which core modules
are always present.

If runtime code consumes `HarnessPolicy` directly forever, policy schema changes
will force runtime rewrites and external runtime adapters will be harder to
support.

## Decision

Add an intermediate `HarnessSpec` layer:

```text
HarnessPolicy -> HarnessSpec -> ModularHarness
```

`HarnessPolicy` remains the strategy artifact. `HarnessSpec` is the runtime
assembly artifact. `ModularHarness` is the executable result.

## Consequences

- Policy generation can evolve without directly changing runtime modules.
- The same policy can later compile to native AdaHarness, LangGraph, OpenAI
  Agents SDK, or Claude Agent SDK-oriented specs.
- Reports can explain both the high-level policy and the actual enabled modules.
- AdaHarness becomes a policy compiler for harnesses, not only an evaluator.
