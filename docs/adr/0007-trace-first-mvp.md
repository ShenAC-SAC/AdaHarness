# ADR 0007: Reduce MVP to Trace-First Harness Diagnostics

## Status

Accepted

## Context

The project had expanded toward a full policy compiler, runtime adapter, project
calibration framework, and reference runtime. That architecture is coherent, but
it is too heavy for the first useful product. Early users should not need to
write adapters, expose runtime hooks, or accept AdaHarness as a control layer
before the tool proves it can make good recommendations.

The most concrete early pain is harness drift: after model, prompt, tool, or
task changes, teams do not know whether existing planning, verification, retry,
and tool-control settings are still appropriate.

## Decision

The MVP will be trace-first:

```text
traces -> metrics -> diagnosis -> suggested policy diff -> report
```

AdaHarness will analyze exported traces and eval results. It will not control
the user's runtime in the MVP.

## Consequences

- `analyze` becomes the primary command.
- Observable trace metrics replace abstract model capability scores as the main
  evidence source.
- `RuntimeBinding`, `ProjectAgentAdapter`, `HarnessSpec`, and the reference
  runtime remain experimental scaffolding.
- Reports must include evidence for every recommendation.
- The project can later reintroduce runtime binding only after trace-based
  diagnostics prove useful.
