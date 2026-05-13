# Architecture

AdaHarness is being reduced to a trace-first harness drift analyzer. The MVP
does not control the user's runtime. It reads traces or eval results from an
existing agent project, computes harness metrics, diagnoses overconstraint or
underconstraint, and suggests policy diffs.

The MVP flow is:

```text
Trace JSONL -> TraceMetrics -> HarnessDiagnosis -> PolicyDiff -> Report
```

With `--out`, the CLI also writes a combined `analysis.json` artifact for CI and
tooling.

This keeps integration light: users can export logs without adopting AdaHarness
modules, adapters, or runtime hooks.

## Package Boundaries

- `adaharness/analysis/` owns trace ingestion, metrics, diagnosis, policy diff
  recommendation, and report rendering.
- `adaharness/integrations/` normalizes richer external trace formats into
  AdaHarness-compatible traces.
- `adaharness/policies/` keeps policy schemas and diff helpers used by reports.
- `adaharness/cli.py` should make `analyze` the main MVP command.
- `adaharness/project/`, `adaharness/adapters/`, `adaharness/specs/`,
  `adaharness/modules/`, and `adaharness/harnesses/` are experimental
  scaffolding from the earlier control-layer direction.

## Trace Contract

The first trace contract should be simple JSONL. Each line is one event:

```json
{"task_id":"t1","event":"verifier","status":"pass","cost":0.002}
{"task_id":"t1","event":"retry","reason":"tool_failure"}
{"task_id":"t1","event":"final","success":true,"cost":0.012,"latency_ms":2200}
```

AdaHarness should prefer observable metrics over abstract model scores:

- verifier catch rate
- verifier cost share
- retry success and waste rate
- planner latency share
- tool failure rate
- tool result ignored rate
- success, cost, and latency deltas

## Experimental Layers

The earlier control-layer architecture remains useful as a future direction, but
it should not define the MVP:

```text
HarnessPolicy -> HarnessSpec -> RuntimeBinding -> runtime hooks
```

Those layers can become valuable after trace-based diagnostics prove that
AdaHarness can give recommendations users trust. Until then, they should stay
out of the primary user path.
