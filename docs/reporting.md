# Reporting

AdaHarness reports should explain harness behavior, not only summarize scores.

## Compare Output

`adaharness compare` emits:

- `results`: aggregate metrics per harness.
- `runs`: task-level `RunResult` records with embedded `RunTrace`.
- `trace_path`: file path for each saved trace when `--out` is provided.

Single-model compare:

```bash
uv run adaharness compare --model small-sim --taskset tasks/eval --out runs/compare.json
```

Model matrix compare:

```bash
uv run adaharness compare --models small-sim,strong-sim --taskset tasks/eval --out runs/matrix.json
```

## Failure Analysis

`adaharness report` renders the metrics table and a compact failure section
grouped by harness and task. The failure lines are derived from `RunResult`
errors and should remain traceable to the corresponding `RunTrace`.
