# Metrics

AdaHarness compares harnesses by measuring both task performance and orchestration
overhead. The goal is to identify the minimal effective harness, not simply the
most complex one.

## Core Metrics

- `success_rate`: fraction of tasks completed by a harness.
- `estimated_cost`: relative cost estimate for running the harness.
- `estimated_latency`: relative latency estimate for running the harness.
- `retry_count`: number of retries implied by the harness policy.
- `harness_lift`: success-rate improvement over the `bare` baseline.
- `harness_tax`: cost multiplier relative to the `bare` baseline.
- `minimal_effective_harness_score`: success adjusted by harness tax.
- `overconstraint_penalty`: cost and latency penalty not justified by lift.
- `adaptation_gain`: adaptive MEH score compared with the best fixed harness.
- `harness_drift_score`: mismatch between an existing policy and a replacement
  model's recommended policy.
- `underconstraint_risk`: expected failure risk when a weak model receives too
  little planning, verification, retry, or tool control.
- `policy_delta`: size of the change between two policies or module specs.

## Interpretation

`bare` is the baseline for relative metrics. A stronger harness is useful when
its lift is large enough to justify its tax. If two harnesses have similar
success rates, prefer the one with the lower tax and simpler policy.

Example report:

```bash
adaharness compare --model small-sim --taskset tasks/eval --out runs/compare.json
adaharness report runs/compare.json
```

The report table is the first place to check whether `adaptive` is choosing a
reasonable tradeoff compared with fixed `bare`, `light`, and `strong` presets.

For model migration, the main question is whether the old harness still fits the
new model. High drift means the user should inspect policy and module diffs
before shipping the replacement model.

Matrix reports compare `model x harness` combinations:

```bash
uv run adaharness compare --models small-sim,strong-sim --taskset tasks/eval --out runs/matrix.json
uv run adaharness report runs/matrix.json
```
