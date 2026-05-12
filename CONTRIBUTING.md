# Contributing to AdaHarness

AdaHarness is an evaluation-first project for learning the minimal effective
harness for a given model, task, budget, and risk level. Keep changes small,
measurable, and tied to the current MVP unless a larger design has been agreed.

## Local Setup

```bash
uv sync --group dev
uv run pytest -q
uv run ruff check .
```

Use Python 3.10 or newer. Commit `uv.lock` when dependencies change. Generated
reports, traces, and experiment outputs belong in `runs/`, which is ignored by git.

## Development Flow

1. Add or update tests in `tests/` for changed behavior.
2. Keep task fixtures in `tasks/eval/` or `tasks/profiler/` minimal and readable.
3. Run `uv run pytest -q` and `uv run ruff check .` before opening a pull request.
4. Include sample CLI output when changing user-facing commands or reports.

## Commit Style

Use explicit Conventional Commit subjects with a scope:

```text
feat(policy): add adaptive budget rule
fix(cli): validate missing taskset path
docs(metrics): explain harness tax
test(evals): cover bare baseline scoring
```

Keep unrelated work in separate commits and pull requests.
