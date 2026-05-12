# Minimal Effective Harness

The minimal effective harness is the lightest orchestration policy that reaches
acceptable task performance for a model, taskset, budget, and risk level.

AdaHarness measures this with:

- `harness_lift`: success improvement over `bare`.
- `harness_tax`: cost multiplier over `bare`.
- `overconstraint_penalty`: cost and latency penalty not justified by lift.
- `minimal_effective_harness_score`: success adjusted by harness tax.
- `adaptation_gain`: adaptive score compared with the best fixed harness.

The practical rule is conservative: if two harnesses have similar success,
prefer the one with lower tax and fewer controls. Strong harnesses are useful
when they create clear lift; otherwise they may become overhead.
