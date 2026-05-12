from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from adaharness.evals.runner import compare_harness_runs
from adaharness.evals.task_schema import load_taskset
from adaharness.harnesses import (
    BARE_HARNESS,
    LIGHT_HARNESS,
    STRONG_HARNESS,
    STRUCTURED_HARNESS,
    build_adaptive_harness,
)
from adaharness.harnesses.base import Harness
from adaharness.harnesses.builder import HarnessBuilder
from adaharness.models import (
    SUPPORTED_PROVIDERS,
    ModelClient,
    ModelConfig,
    build_model_client,
    build_model_config,
)
from adaharness.policies.artifacts import PolicyRecommendation
from adaharness.policies.generator import recommend_policy
from adaharness.policies.migration import build_migration_report
from adaharness.policies.refinement import load_traces, refine_policy_from_traces
from adaharness.policies.schema import BUDGET_LEVELS, RISK_LEVELS, HarnessPolicy
from adaharness.profiler.profile_schema import ModelProfile
from adaharness.profiler.runner import run_profiler
from adaharness.runtime.budget import Budget
from adaharness.runtime.results import RunResult
from adaharness.specs import compile_policy_to_spec
from adaharness.specs.harness_spec import HarnessSpec


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _load_profile(path: Path) -> ModelProfile:
    return ModelProfile.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _load_policy(path: Path) -> tuple[HarnessPolicy, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "policy" in data:
        recommendation = PolicyRecommendation.from_dict(data)
        return recommendation.policy, {
            "source_artifact": str(path),
            "recommendation": {
                "model_name": recommendation.model_name,
                "risk": recommendation.risk,
                "budget": recommendation.budget,
                "source": recommendation.source,
                "schema_version": recommendation.schema_version,
            },
        }
    return HarnessPolicy.from_dict(data), {"source_artifact": str(path)}


def _load_harness_spec(path: Path) -> HarnessSpec:
    return HarnessSpec.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _model_config_from_args(args: argparse.Namespace) -> ModelConfig:
    return build_model_config(args.model, provider=args.provider, base_url=args.base_url)


def _model_client_from_args(args: argparse.Namespace) -> ModelClient:
    if not args.live and args.provider not in {"synthetic", "mock"}:
        raise ValueError("real model providers require --live")
    return build_model_client(_model_config_from_args(args))


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _selected_harnesses(names: list[str], profile: ModelProfile) -> list[Harness]:
    harnesses = {
        "bare": BARE_HARNESS,
        "light": LIGHT_HARNESS,
        "structured": STRUCTURED_HARNESS,
        "strong": STRONG_HARNESS,
        "adaptive": build_adaptive_harness(profile),
    }
    selected = names or list(harnesses)
    unknown = [name for name in selected if name not in harnesses]
    if unknown:
        supported = ", ".join(harnesses)
        raise ValueError(f"Unsupported harness {unknown[0]!r}. Expected one of: {supported}")
    return [harnesses[name] for name in selected]


def _run_records(out_path: Path | None, runs: list[RunResult]) -> list[dict[str, object]]:
    trace_paths = _write_trace_files(out_path, runs) if out_path else {}
    records = []
    for run in runs:
        record = run.to_dict()
        trace_path = trace_paths.get(run.trace.run_id)
        if trace_path is not None:
            record["trace_path"] = str(trace_path)
        records.append(record)
    return records


def _write_trace_files(out_path: Path, runs: list[RunResult]) -> dict[str, Path]:
    trace_dir = out_path.with_suffix("")
    trace_dir = trace_dir.parent / f"{trace_dir.name}-traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for run in runs:
        trace_path = trace_dir / f"{run.trace.run_id}.json"
        trace_path.write_text(json.dumps(run.trace.to_dict(), indent=2) + "\n", encoding="utf-8")
        paths[run.trace.run_id] = trace_path
    return paths


def cmd_profile(args: argparse.Namespace) -> int:
    taskset = Path(args.taskset) if args.taskset else None
    profile = run_profiler(_model_config_from_args(args), taskset=taskset)
    data = profile.to_dict()
    if args.out:
        _write_json(Path(args.out), data)
    print(json.dumps(data, indent=2))
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    profile = _load_profile(Path(args.profile))
    recommendation = recommend_policy(profile, risk=args.risk, budget=args.budget)
    data = recommendation.to_dict()
    if args.out:
        _write_json(Path(args.out), data)
    print(json.dumps(data, indent=2))
    return 0


def cmd_assemble(args: argparse.Namespace) -> int:
    policy, metadata = _load_policy(Path(args.policy))
    spec = compile_policy_to_spec(policy, name=args.name, metadata=metadata)
    data = spec.to_dict()
    if args.out:
        _write_json(Path(args.out), data)
    print(json.dumps(data, indent=2))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    tasks = load_taskset(Path(args.taskset))
    out_path = Path(args.out) if args.out else None
    model_names = _split_csv(args.models) or ([args.model] if args.model else [])
    if not model_names:
        raise ValueError("compare requires --model or --models")
    comparisons = []
    for model_name in model_names:
        config = build_model_config(model_name, provider=args.provider, base_url=args.base_url)
        profile = _load_profile(Path(args.profile)) if args.profile else run_profiler(config)
        harnesses = _selected_harnesses(_split_csv(args.harnesses), profile)
        metrics, runs = compare_harness_runs(profile, harnesses, tasks)
        comparisons.append(
            {
                "model_name": profile.model_name,
                "profile": profile.to_dict(),
                "task_count": len(tasks),
                "results": [item.to_dict() for item in metrics],
                "runs": _run_records(out_path, runs),
            }
        )

    data = comparisons[0] if len(comparisons) == 1 else {"task_count": len(tasks), "comparisons": comparisons}
    if args.out:
        _write_json(out_path or Path(args.out), data)
    print(json.dumps(data, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    spec = _load_harness_spec(Path(args.harness_spec))
    harness = HarnessBuilder().build(spec)
    tasks = load_taskset(Path(args.task))
    model = _model_client_from_args(args)
    results = [harness.run(task, model, budget=Budget()) for task in tasks]
    out_path = Path(args.out) if args.out else None
    data = {
        "model_name": model.model_name,
        "harness_spec": spec.to_dict(),
        "task_count": len(tasks),
        "runs": _run_records(out_path, results),
    }
    if out_path:
        _write_json(out_path, data)
    print(json.dumps(data, indent=2))
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    from_profile = _load_profile(Path(args.from_profile))
    to_profile = _load_profile(Path(args.to_profile))
    from_policy, _ = _load_policy(Path(args.from_policy))
    report = build_migration_report(
        from_profile=from_profile,
        to_profile=to_profile,
        from_policy=from_policy,
        risk=args.risk,
        budget=args.budget,
    )
    data = report.to_dict()
    if args.out:
        _write_json(Path(args.out), data)
    print(json.dumps(data, indent=2))
    return 0


def cmd_refine(args: argparse.Namespace) -> int:
    policy, _ = _load_policy(Path(args.policy))
    traces = load_traces(Path(args.trace))
    refinement = refine_policy_from_traces(policy, traces, name=args.name)
    data = refinement.to_dict()
    if args.out:
        _write_json(Path(args.out), data)
    print(json.dumps(data, indent=2))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.run).read_text(encoding="utf-8"))
    if "comparisons" in data:
        print(_render_matrix_report(data))
        return 0

    print(_render_single_report(data))
    return 0


def _render_single_report(data: dict[str, Any]) -> str:
    lines = [
        f"# AdaHarness Report: {data['model_name']}",
        "",
        f"- Task count: {data['task_count']}",
        "",
        "| Harness | Success | Cost | Tax | Lift | MEH | Penalty | Adapt Gain |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in data["results"]:
        lines.append(
            "| {harness_name} | {success_rate:.2f} | {estimated_cost:.2f} | "
            "{harness_tax:.2f} | {harness_lift:.2f} | "
            "{minimal_effective_harness_score:.2f} | {overconstraint_penalty:.2f} | "
            "{adaptation_gain:.2f} |".format(**item)
        )
    lines.extend(_failure_reason_lines(data.get("runs", [])))
    return "\n".join(lines)


def _render_matrix_report(data: dict[str, Any]) -> str:
    lines = [
        "# AdaHarness Matrix Report",
        "",
        f"- Task count: {data['task_count']}",
        "",
        "| Model | Harness | Success | Cost | Tax | Lift | MEH | Adapt Gain |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for comparison in data["comparisons"]:
        for item in comparison["results"]:
            lines.append(
                "| {model_name} | {harness_name} | {success_rate:.2f} | {estimated_cost:.2f} | "
                "{harness_tax:.2f} | {harness_lift:.2f} | "
                "{minimal_effective_harness_score:.2f} | {adaptation_gain:.2f} |".format(
                    model_name=comparison["model_name"],
                    **item,
                )
            )
    for comparison in data["comparisons"]:
        lines.extend(_failure_reason_lines(comparison.get("runs", []), model_name=comparison["model_name"]))
    return "\n".join(lines)


def _failure_reason_lines(runs: list[dict[str, Any]], model_name: str | None = None) -> list[str]:
    failures = [run for run in runs if run.get("errors")]
    if not failures:
        return []

    title = "Failure Reasons" if model_name is None else f"Failure Reasons: {model_name}"
    lines = ["", f"## {title}", ""]
    for run in failures:
        errors = "; ".join(run["errors"])
        lines.append(f"- `{run['harness_name']}` / `{run['task_id']}`: {errors}")
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adaharness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    profile = subparsers.add_parser("profile", help="Run model profiler")
    profile.add_argument("--model", required=True)
    profile.add_argument("--provider", choices=SUPPORTED_PROVIDERS, default="synthetic")
    profile.add_argument("--base-url")
    profile.add_argument("--taskset")
    profile.add_argument("--out")
    profile.set_defaults(func=cmd_profile)

    recommend = subparsers.add_parser("recommend", help="Recommend a harness policy")
    recommend.add_argument("--profile", required=True)
    recommend.add_argument("--risk", choices=RISK_LEVELS, default="medium")
    recommend.add_argument("--budget", choices=BUDGET_LEVELS, default="standard")
    recommend.add_argument("--out")
    recommend.set_defaults(func=cmd_recommend)

    assemble = subparsers.add_parser("assemble", help="Compile a policy into a harness spec")
    assemble.add_argument("--policy", required=True)
    assemble.add_argument("--name", default="compiled_harness")
    assemble.add_argument("--out")
    assemble.set_defaults(func=cmd_assemble)

    compare = subparsers.add_parser("compare", help="Compare harness presets")
    compare.add_argument("--model")
    compare.add_argument("--models")
    compare.add_argument("--provider", choices=SUPPORTED_PROVIDERS, default="synthetic")
    compare.add_argument("--base-url")
    compare.add_argument("--harnesses")
    compare.add_argument("--profile")
    compare.add_argument("--taskset", required=True)
    compare.add_argument("--out")
    compare.set_defaults(func=cmd_compare)

    run = subparsers.add_parser("run", help="Run a task with a compiled harness spec")
    run.add_argument("--harness-spec", required=True)
    run.add_argument("--task", required=True)
    run.add_argument("--model", required=True)
    run.add_argument("--provider", choices=SUPPORTED_PROVIDERS, default="synthetic")
    run.add_argument("--base-url")
    run.add_argument("--live", action="store_true")
    run.add_argument("--out")
    run.set_defaults(func=cmd_run)

    migrate = subparsers.add_parser("migrate", help="Compare current and recommended harness policy")
    migrate.add_argument("--from-profile", required=True)
    migrate.add_argument("--to-profile", required=True)
    migrate.add_argument("--from-policy", required=True)
    migrate.add_argument("--risk", choices=RISK_LEVELS, default="medium")
    migrate.add_argument("--budget", choices=BUDGET_LEVELS, default="standard")
    migrate.add_argument("--out")
    migrate.set_defaults(func=cmd_migrate)

    refine = subparsers.add_parser("refine", help="Propose policy updates from run traces")
    refine.add_argument("--policy", required=True)
    refine.add_argument("--trace", required=True)
    refine.add_argument("--name", default="refined_harness")
    refine.add_argument("--out")
    refine.set_defaults(func=cmd_refine)

    report = subparsers.add_parser("report", help="Render a compare run as Markdown")
    report.add_argument("run")
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
