# Roadmap

AdaHarness is now centered on a lighter MVP:

```text
Agent traces -> harness metrics -> diagnosis -> suggested policy diff -> report
```

The CLI should analyze exported traces first:

```text
analyze -> diagnose -> recommend diff -> report
```

Policy compilers, runtime bindings, project adapters, and `ModularHarness`
remain experimental scaffolding. They are not the MVP product boundary.

## Completed Foundation

- Harness policy, controller spec, binding, project adapter, and reference
  runtime scaffolding.
- Generic external trace normalization.
- Migration and policy-diff prototypes.
- Trace analyzer that writes metrics, diagnosis, policy diff, and combined
  structured output.
- Trace validation warnings, diagnostic confidence, and configurable diagnostic
  thresholds.
- Minimal `TraceRecorder` SDK for host projects that want a small JSONL writer.

## Phase 1 Trace Ingestion

Goal: make AdaHarness useful without runtime integration.

- Define a small JSONL trace event format.
- Load traces from one or more files.
- Validate canonical events, missing finals, duplicate finals, and missing cost
  or latency evidence.
- Accept traces exported by user projects without requiring adapters.

Acceptance: `adaharness analyze --traces traces.jsonl` can load events and
produce a basic metrics object.

## Phase 2 Harness Diagnostics

Goal: diagnose over-control and under-control from observable signals.

- Compute verifier catch rate, verifier cost share, retry success rate, retry
  waste rate, planner latency share, tool failure rate, and success rate.
- Add explicit overconstraint and underconstraint signals.
- Include evidence lines, confidence, evidence counts, and rule thresholds for
  every diagnosis.

Acceptance: the report can explain why a harness looks too heavy, too weak, or
roughly appropriate.

## Phase 3 Policy Diff Recommendation

Goal: suggest changes without controlling the user's runtime.

- Load an optional current policy JSON.
- Recommend changes such as `always -> selective`, `explicit -> light`, or
  `aggressive -> bounded`.
- Attach a reason and evidence to every suggested change.

Acceptance: `analyze` writes `analysis.json`, `policy_diff.json`, and a
human-readable report.

## Phase 4 Migration Report

Goal: compare old and new traces after model, prompt, tool, or task changes.

- Accept `--baseline-traces` and `--candidate-traces`.
- Report drift in success, cost, latency, verifier usefulness, retry usefulness,
  and tool failure behavior.
- Recommend whether the current harness should be weakened, strengthened, or
  left unchanged.

Acceptance: migration reports explain whether the old harness still fits the new
system behavior.

## Phase 5 Minimal Trace SDK

Goal: reduce integration friction further.

- Add a small `TraceRecorder` helper for agent projects. Completed.
- Keep it optional; users can still export JSONL manually. Completed.
- Do not add runtime control or hook mutation. Completed.

Acceptance: a host project can record AdaHarness-compatible traces in a few
lines of code.

## Experimental

These pieces remain in the codebase but are not the MVP path:

- `ProjectAgentAdapter`
- `RuntimeBinding`
- `HarnessSpec` compiler
- reference `ModularHarness`
- online adaptation and controller binding
