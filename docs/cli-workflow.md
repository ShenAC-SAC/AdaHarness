# CLI Workflow

The MVP CLI is an analysis tool for traces exported by an existing agent
project. It should not be the production agent runner and should not require the
project to adopt AdaHarness runtime modules.

## Primary Path

```bash
adaharness analyze \
  --traces traces/new-model.jsonl \
  --current-policy policies/current.json \
  --out reports/harness-drift.md
```

Expected outputs:

```text
reports/harness-drift.md
reports/harness-drift.metrics.json
reports/harness-drift.diagnosis.json
reports/harness-drift.policy-diff.json
```

## Trace Format

The initial trace format is JSONL. Each line is an event:

```json
{"task_id":"t1","event":"planner","latency_ms":320}
{"task_id":"t1","event":"verifier","status":"pass","cost":0.002}
{"task_id":"t1","event":"retry","reason":"tool_failure"}
{"task_id":"t1","event":"final","success":true,"cost":0.012,"latency_ms":2200}
```

## Experimental Commands

Existing commands such as `profile`, `compare`, `assemble`, `calibrate`, and
reference `run` remain useful for experiments and CI smoke tests. They are not
the main MVP path.
