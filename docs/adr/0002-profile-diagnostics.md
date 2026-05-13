# ADR 0002: Keep Profile Scalars and Add Diagnostic Scores

## Status

Accepted

Current scope: profiler/lab compatibility. ADR 0007 makes trace evidence, not
abstract profile scores, the primary MVP input.

## Context

Policy generation and synthetic evaluation already depend on top-level
capability scalars such as `planning`, `tool_use`, and `recovery`. Replacing
those fields with nested score objects would force unrelated modules to change
before task-backed profiling is mature.

## Decision

Keep scalar capability fields as the compatibility contract and add nested
`CapabilityScore` diagnostics for evidence, confidence, and failed cases.
Profiler tasksets produce diagnostic scores, weaknesses, and recommended
controls, while existing rule-based policy selection can continue to use scalar
averages.

## Consequences

- Legacy profile JSON continues to load.
- Reports and future harness generators can explain weak capabilities.
- Capability schema can evolve without rewriting policy and eval modules.
- The profiler remains deterministic until real task execution is connected.
