# Repository Guidelines

## Project Structure & Module Organization

AdaHarness is a trace-first harness drift analyzer for LLM agent projects. Core MVP code lives in `adaharness/analysis/` for trace ingestion, metrics, diagnosis, policy diffs, and reports. `adaharness/cli.py` exposes the CLI, with `analyze` as the main command. `policies/` keeps policy schemas and recommendation helpers. `adapters/`, `project/`, `specs/`, `modules/`, and `harnesses/` are experimental scaffolding from the earlier runtime-control direction; do not expand them unless the task is explicitly about experiments. Tests live in `tests/`, examples in `examples/`, and generated outputs in `runs/`.

## Build, Test, and Development Commands

- `uv sync --group dev` creates the local `.venv`, installs the package, and records versions in `uv.lock`.
- `uv run pytest -q` runs the full test suite configured by `pyproject.toml`.
- `uv run ruff check .` runs lint checks with the repo’s Python 3.10 and 100-column settings.
- `uv run adaharness analyze --traces examples/traces/overconstrained_harness.jsonl --current-policy examples/policies/heavy_policy.json --out runs/harness-drift.md` runs the MVP trace analysis flow.
- `uv run python -m compileall adaharness tests` catches syntax issues before CI.

## Coding Style & Naming Conventions

Use Python 3.10+ typing syntax such as `list[Harness]` and `dict[str, Any]`. Keep imports grouped by standard library, third-party, then local modules. Follow Ruff defaults with `line-length = 100`. Prefer small dataclass-like schema objects and explicit `to_dict`/`from_dict` conversions where existing modules already use that pattern. Name tests and functions descriptively, for example `test_relative_metrics_use_bare_baseline`.

## Testing Guidelines

The test suite uses `unittest` style under pytest discovery. Add tests in `tests/test_*.py`, with classes ending in `Tests` and methods beginning with `test_`. Prioritize trace loading, metrics, diagnosis, policy diff recommendations, and CLI artifacts when MVP contracts change. Keep JSON/JSONL fixtures minimal and place example traces under `examples/traces/`.

## Commit & Pull Request Guidelines

Use explicit Conventional Commit-style subjects: `feat(scope): ...`, `fix(scope): ...`, `test(scope): ...`, `docs(scope): ...`, or `chore(scope): ...`. The scope should name the touched area, such as `cli`, `policy`, `metrics`, `tasks`, or `docs`. Examples: `feat(policy): add adaptive budget rule`, `fix(cli): validate missing taskset path`. Keep unrelated changes separate. Pull requests should describe the behavior changed, list commands run, link any issue or design note, and include sample CLI output when changing reports, metrics, or user-facing command behavior.

## Security & Configuration Tips

Do not commit secrets or real model credentials. Use `.env.example` for documented environment variables and keep local outputs, traces, and experiment artifacts in `runs/`.

## Working Style

- Think before coding. Do not guess when requirements are ambiguous; state assumptions explicitly.
- If multiple interpretations are plausible, present them instead of silently picking one.
- Prefer the simplest change that fully solves the task. Avoid speculative features, abstractions, or extra configurability.
- Make surgical edits only. Do not refactor adjacent code, reformat unrelated files, or rewrite comments unless the task requires it.
- Remove only the code that your own change makes obsolete. Mention unrelated issues separately.
- Convert requests into concrete success criteria before implementation. For multi-step work, keep a short plan and verify each step.
- If critical context is missing and the next change would be hard to undo, ask before making it.

## Done Means

- The requested behavior is implemented.
- Only task-relevant files and lines were changed.
- Appropriate verification was run, or the lack of verification is stated explicitly.
