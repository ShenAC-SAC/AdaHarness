# ADR 0008: Keep Runtime Scaffolding Experimental

## Status

Accepted

## Context

AdaHarness previously explored a heavier architecture:

```text
HarnessPolicy -> HarnessSpec -> RuntimeBinding -> ProjectAgentAdapter
```

That path can eventually support runtime integration, but it is too heavy for
the current MVP. Early users should not need to adopt AdaHarness modules, write
adapters, or expose runtime hooks before seeing value.

The MVP is now:

```text
exported traces -> metrics -> diagnosis -> suggested policy diff -> report
```

## Decision

Keep the existing adapter, project, spec, module, and reference harness code in
the repository as experimental scaffolding. Do not delete it immediately, but do
not promote it in README quick starts, primary docs, or new MVP work.

The experimental packages are:

- `adaharness/adapters/`
- `adaharness/project/`
- `adaharness/specs/`
- `adaharness/modules/`
- `adaharness/harnesses/`

## Consequences

This avoids churn and preserves tested design work while the trace analyzer is
validated. It also creates a clear rule for future development: new user-facing
work should improve trace ingestion, diagnostics, policy diffs, reports, or the
minimal trace SDK unless explicitly scoped as experimental.

Revisit deletion or extraction if experimental code starts confusing users,
creating maintenance drag, or forcing API compatibility before the MVP proves
value.
