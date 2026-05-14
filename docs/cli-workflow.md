# CLI Workflow

The CLI is an analysis tool for traces exported by an existing agent project. It
does not run the production agent and does not require AdaHarness runtime
modules.

## Primary Path

```bash
adaharness analyze \
  --traces traces/new-model.jsonl \
  --diagnostics-config examples/diagnostics/default.toml \
  --current-policy policies/current.json \
  --out reports/harness-drift.md
```

Expected outputs:

```text
reports/harness-drift.md
reports/harness-drift.analysis.json
reports/harness-drift.metrics.json
reports/harness-drift.diagnosis.json
reports/harness-drift.policy-diff.json
```

`analysis.json` includes the diagnostics config, trace warnings, metrics,
fit verdict, diagnosis signals, and suggested policy diff in one
machine-readable artifact.

## Trace Format

The initial trace format is JSONL. Each line is an event:

```json
{"task_id":"t1","event":"planner","latency_ms":320}
{"task_id":"t1","event":"verifier","status":"pass","cost":0.002}
{"task_id":"t1","event":"retry","reason":"tool_failure"}
{"task_id":"t1","event":"final","success":true,"cost":0.012,"latency_ms":2200}
```

Canonical MVP events are `model_call`, `planner`, `verifier`, `retry`,
`tool_call`, `tool_result_ignored`, `subagent`, `context`, and `final`.

## Diagnostics Config

Diagnostic thresholds are heuristics. Override them with TOML:

```toml
[diagnostics.verifier_overconstraint]
min_events = 20
max_catch_rate = 0.05
min_cost_share = 0.20
```
