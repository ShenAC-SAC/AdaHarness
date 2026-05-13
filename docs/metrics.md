# Trace Format and Metrics

The MVP analyzes traces exported by an existing agent project. It does not need
AdaHarness to run the agent or control runtime hooks.

## Trace Format

Use JSONL first. Each line is one event:

```json
{"task_id":"t1","event":"planner","latency_ms":320}
{"task_id":"t1","event":"verifier","status":"pass","cost":0.002}
{"task_id":"t1","event":"retry","reason":"tool_failure"}
{"task_id":"t1","event":"tool_call","status":"failed","reason":"timeout"}
{"task_id":"t1","event":"final","success":true,"cost":0.012,"latency_ms":2200}
```

Required fields:

- `task_id`: stable task or eval case identifier.
- `event`: event type such as `planner`, `verifier`, `retry`, `tool_call`, or
  `final`.

Canonical MVP event names:

```text
model_call
planner
verifier
retry
tool_call
tool_result_ignored
subagent
context
final
```

Optional fields:

- `status`: `pass`, `fail`, `success`, or `failed`.
- `success`: boolean final outcome for `final` events.
- `cost`, `latency_ms`, `tokens`: observed cost and overhead.
- `model`, `policy`, `control`, `reason`: grouping and explanation metadata.

## MVP Metrics

AdaHarness prefers observable harness signals over abstract model capability
scores:

- `success_rate`: final success rate across traced tasks.
- `verifier_catch_rate`: fraction of verifier events that caught a failure.
- `verifier_cost_share`: cost share spent on verifier events.
- `planner_latency_share`: latency share spent on planner events.
- `retry_success_rate`: fraction of retried tasks that eventually succeeded.
- `retry_waste_rate`: retry rate on tasks that still failed.
- `failed_without_retry_rate`: failed tasks that had no retry event.
- `tool_failure_rate`: failed tool calls over all tool calls.
- `tool_result_ignored_rate`: tasks that emitted `tool_result_ignored`.

## Structured Output

`adaharness analyze --out reports/harness-drift.md` writes:

```text
reports/harness-drift.md
reports/harness-drift.analysis.json
reports/harness-drift.metrics.json
reports/harness-drift.diagnosis.json
reports/harness-drift.policy-diff.json
```

`analysis.json` combines the structured result for downstream CI. The other
sidecars are stable slices for tools that only need metrics, diagnosis, or
policy diffs.

## Trace Validation

`analyze` reports trace quality warnings for:

- unknown event names
- missing final events
- multiple final events for one task
- missing cost evidence
- missing latency evidence

Warnings do not fail analysis by default. They tell the user when a metric is
based on incomplete trace evidence.

## Diagnostics Config

Diagnostic rules are heuristics. Defaults are intentionally small enough for the
bundled examples, but production projects should raise event-count thresholds as
their eval suites mature.

```toml
[diagnostics.verifier_overconstraint]
min_events = 20
max_catch_rate = 0.05
min_cost_share = 0.20

[diagnostics.confidence]
medium_evidence_count = 50
high_evidence_count = 200
```

Run with:

```bash
adaharness analyze --traces traces.jsonl --diagnostics-config diagnostics.toml
```
