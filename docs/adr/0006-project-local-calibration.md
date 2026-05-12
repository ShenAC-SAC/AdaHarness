# ADR 0006: Make Calibration Project-Local

## Status

Accepted

## Context

AdaHarness originally exposed standalone model profiling and reference runtime
commands as the main user path. That is useful for smoke tests, but the policy
value is weak when detached from the user's real agent runtime, prompts, tools,
tasks, and traces.

A harness control policy is only deployable when it reflects the host project.
The same model can require different planning, verification, retry, and tool
control in different agent systems.

## Decision

AdaHarness will be embedded-first. The primary user path is project-local
calibration:

```text
ProjectAgentAdapter -> ProjectRunTrace -> AgentSystemProfile
  -> HarnessPolicy -> HarnessSpec -> RuntimeBinding
```

Standalone CLI/reference-runtime flows remain as lab and CI utilities, not the
main product story. The host agent project owns provider credentials, model
configuration, prompts, tools, state, and production execution.

## Consequences

- Documentation should present AdaHarness as a project calibration and control
  binding layer.
- CLI commands should evolve toward `calibrate`, `bind`, and `validate`.
- `profile`, `compare`, `assemble`, and reference `run` remain compatibility or
  lab commands.
- New APIs should accept project adapters, imported traces, or host-provided
  profiles rather than forcing duplicate provider configuration.
