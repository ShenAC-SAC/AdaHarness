# ADR 0009: Remove Runtime Scaffolding From the MVP

## Status

Accepted

## Context

ADR 0008 kept the older runtime-control architecture in the repository as
experimental scaffolding. That avoided churn, but it also kept the project
looking like a framework: adapters, model clients, profilers, harness presets,
runtime modules, and policy compilers were still present in code, CLI commands,
tests, and docs.

The current product direction is narrower. AdaHarness should be a lightweight
tool for agent developers who already have a runtime. Its job is to analyze
exported traces after a model, prompt, tool, or task change and recommend
evidence-backed harness policy diffs.

## Decision

Supersede ADR 0008. Remove the experimental runtime scaffolding from the active
codebase instead of hiding it.

The retained MVP path is:

```text
exported traces -> validation -> metrics -> diagnosis -> policy diff -> report
```

The retained packages are:

- `adaharness/analysis/`
- `adaharness/trace/`
- `adaharness/api.py`
- `adaharness/cli.py`

The CLI keeps `analyze` as the stable command. AdaHarness does not run user
agent commands, compile executable harness specs, bind runtime hooks, profile
models, or manage provider credentials.

## Consequences

- The project becomes easier to explain and install.
- The public API is trace-first instead of runtime-first.
- Historical ADRs remain as project history, but primary docs must not present
  removed scaffolding as available functionality.
- Future runtime integration must be justified by proven trace-analysis value and
  reintroduced as a separate, explicit design.
