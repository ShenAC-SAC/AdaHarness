# ADR 0010: Add Grouped Trace Analysis Without Moving Metrics Responsibility

## Status

Accepted

## Context

AdaHarness now reports a single-trace fit verdict. That verdict can be misleading
when one trace set contains multiple models, policies, or task types. Aggregating
those dimensions can hide the actual model-harness mismatch the user is trying
to diagnose.

The project still needs to stay lightweight. Grouping should not introduce a
runtime adapter layer, a query engine, or a broad data frame abstraction.

## Decision

Add grouping as a thin analysis orchestration layer:

- `TraceEvent` owns canonical event fields, including `model`, `policy`, and
  `task_type`.
- `compute_trace_metrics(...)` continues to compute metrics for one event set.
- `adaharness.analysis.grouping` slices events by explicit dimensions.
- `adaharness.analysis.result` packages one analyzed event set into a stable
  artifact shape.
- `analyze_traces(..., group_by=...)` returns the aggregate result plus optional
  per-group results.

The CLI exposes grouping as a comma-separated option:

```bash
adaharness analyze --traces traces.jsonl --group-by model,policy
```

If `--group-by` is omitted and the trace contains multiple model, policy, or
task-type values, AdaHarness emits trace quality warnings instead of silently
pretending the aggregate verdict is clean.

## Consequences

- Grouped analysis is available without changing metric computation semantics.
- Future migration and policy-comparison reports can reuse `AnalysisResult`.
- Aggregate reports remain backward compatible for users who pass one homogeneous
  trace set.
- Grouping is intentionally explicit; AdaHarness does not infer framework
  structure from arbitrary logs.
