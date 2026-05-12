# AdaHarness Bench

AdaHarness Bench is intentionally lightweight. The first benchmark is a small
set of synthetic tasks that make harness behavior visible before heavier
benchmarks or real-world task suites are added.

## Task Families

- Planning and dependency ordering.
- Tool-use fidelity.
- Context discipline.
- Recovery from failed observations.
- Cost and budget sensitivity.
- Delegation judgment.

## Leaderboard Shape

The primary comparison is `model x harness`, not model-only ranking:

```bash
uv run adaharness compare \
  --models small-sim,strong-sim \
  --harnesses bare,light,structured,strong,adaptive \
  --taskset tasks/eval \
  --out runs/model-harness-matrix.json

uv run adaharness report runs/model-harness-matrix.json
```

This makes the core claim testable: smaller models may gain from stronger
harnesses, while stronger models may lose efficiency when over-constrained.
