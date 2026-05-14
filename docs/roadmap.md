# Roadmap

AdaHarness is centered on a lightweight MVP:

```text
agent traces -> harness metrics -> diagnosis -> suggested policy diff -> report
```

The project is intentionally not a runtime, model profiler, harness builder, or
policy compiler.

## Completed Foundation

- Load JSONL traces from one or more files.
- Validate missing finals, duplicate finals, unknown events, and missing cost or
  latency evidence.
- Compute verifier, planner, retry, tool-use, cost, latency, and success metrics.
- Diagnose overconstraint and underconstraint signals.
- Summarize single-trace evidence into a fit verdict.
- Group single-trace analysis by model, policy, or task type.
- Attach evidence, confidence, evidence counts, and rule thresholds to
  diagnostics.
- Recommend advisory policy diffs from signals.
- Render Markdown reports and structured JSON sidecars.
- Provide a minimal `TraceRecorder` SDK that only writes JSONL events.

## Phase 1: Better Trace Ergonomics

Goal: make trace export easy without runtime integration.

- Improve trace format docs and examples.
- Add more validation messages for common malformed traces.
- Add examples for direct JSONL export and `TraceRecorder`.

Acceptance: a user can add useful traces to an existing agent project without
writing an adapter or using AdaHarness to launch the agent.

## Phase 2: Model Migration Reports

Goal: compare old and new traces after an LLM change.

- Accept baseline and candidate trace sets.
- Report drift in success, cost, latency, verifier usefulness, retry usefulness,
  and tool failure behavior.
- Recommend whether controls should be weakened, strengthened, or left alone.

Acceptance: reports explain whether the old harness still fits the new model.

## Phase 3: Stronger Policy Diff Semantics

Goal: make recommendations easier to act on without becoming a runtime.

- Document the lightweight policy vocabulary.
- Preserve current policy fields even when only one control changes.
- Include before/after policy JSON as an optional artifact.

Acceptance: users can map AdaHarness advice back to their own harness config.

## Explicit Non-Roadmap

The following are not planned for the MVP:

- running user agent commands
- built-in workload suites
- model provider clients
- deterministic model profilers
- project adapters
- reference harness runtime
- policy-to-runtime compilers
