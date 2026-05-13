# Architecture

AdaHarness is a trace-first harness drift analyzer. It does not control the
user's runtime. It reads traces from an existing agent project, computes harness
metrics, diagnoses overconstraint or underconstraint, and suggests policy diffs.

The maintained flow is:

```text
TraceRecorder / JSONL traces
-> TraceValidation
-> TraceMetrics
-> HarnessDiagnosis
-> PolicyDiff
-> Report
```

With `--out`, the CLI writes a Markdown report plus structured sidecars for CI
and dashboards.

## Package Boundaries

- `adaharness/analysis/` owns trace ingestion, validation, metrics, diagnosis,
  policy diff recommendation, and report rendering.
- `adaharness/trace/` owns optional JSONL recording helpers for host projects.
  It writes events only; it must not mutate or control the host runtime.
- `adaharness/api.py` exposes a small `analyze_traces(...)` API for code users.
- `adaharness/cli.py` exposes `adaharness analyze`.

Removed runtime-control layers such as adapters, model clients, profilers,
reference harnesses, compiled specs, and project calibration are not part of the
MVP.

## Trace Contract

The trace contract is simple JSONL. Each line is one event:

```json
{"task_id":"t1","event":"planner","latency_ms":320}
{"task_id":"t1","event":"verifier","status":"pass","cost":0.002}
{"task_id":"t1","event":"retry","reason":"tool_failure"}
{"task_id":"t1","event":"final","success":true,"cost":0.012,"latency_ms":2200}
```

Required fields:

- `task_id`
- `event`

Important optional fields:

- `status`
- `success`
- `cost`
- `latency_ms`
- `tokens`
- `model`
- `policy`
- `control`
- `reason`

## Metrics and Diagnostics

AdaHarness prefers observable trace evidence over abstract model scores:

- verifier catch rate
- verifier cost share
- retry success and waste rate
- planner latency share
- tool failure rate
- tool result ignored rate
- success, cost, and latency evidence

Diagnostic rules are configurable heuristics. Reports include rule thresholds,
observed values, evidence counts, confidence, and trace quality warnings so
recommendations stay auditable.
