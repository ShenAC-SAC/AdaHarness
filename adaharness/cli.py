from __future__ import annotations

import argparse
import importlib
from importlib.resources import files
import json
from pathlib import Path
import sys
from typing import Any

from adaharness.analysis import (
    compute_trace_metrics,
    diagnose_harness,
    load_diagnostic_config,
    load_trace_events,
    recommend_policy_changes,
    render_analysis_report,
    validate_trace_events,
)
from adaharness.capture import capture_command_runs, load_capture_tasks
from adaharness.config import AdaHarnessConfig, load_config
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
from adaharness.integrations import import_external_trace
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
from adaharness.project import ProjectAgentAdapter, calibrate_project
from adaharness.profiler.profile_schema import ModelProfile
from adaharness.profiler.runner import run_profiler
from adaharness.runtime.budget import Budget
from adaharness.runtime.results import RunResult
from adaharness.specs import compile_policy_to_spec
from adaharness.specs.harness_spec import HarnessSpec


INIT_TEMPLATE_FILES = (
    ("README.md", "README.md"),
    ("diagnostics/default.toml", "diagnostics/default.toml"),
    ("policies/current-policy.json", "policies/current-policy.json"),
    ("tasks/sample-tasks.jsonl", "tasks/sample-tasks.jsonl"),
    ("traces/overconstrained_harness.jsonl", "traces/overconstrained_harness.jsonl"),
    ("traces/undercontrolled_tool_use.jsonl", "traces/undercontrolled_tool_use.jsonl"),
)


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


def _load_policy_dict(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("policy", data)


def _project_config_from_args(args: argparse.Namespace) -> AdaHarnessConfig | None:
    config_path = getattr(args, "config", None)
    if not config_path:
        return None
    return load_config(config_path, env_file=getattr(args, "env_file", None))


def _config_root(config: AdaHarnessConfig) -> Path:
    return Path(config.source_path).parent if config.source_path else Path.cwd()


def _resolve_config_path(config: AdaHarnessConfig, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else _config_root(config) / path


def _load_project_adapter(config: AdaHarnessConfig, adapter_path: str | None = None) -> ProjectAgentAdapter:
    target = adapter_path or config.project.adapter
    if not target:
        raise ValueError("calibrate requires [project].adapter or --adapter")
    if ":" not in target:
        raise ValueError("adapter must use 'module.path:ObjectName' format")

    module_name, object_name = target.split(":", 1)
    root = str(_config_root(config))
    if root not in sys.path:
        sys.path.insert(0, root)
    module = importlib.import_module(module_name)
    factory = getattr(module, object_name)
    adapter = factory() if isinstance(factory, type) else factory
    if not hasattr(adapter, "run_task") or not hasattr(adapter, "capabilities"):
        raise TypeError("project adapter must define capabilities() and run_task(...)")
    return adapter


def _model_config_from_args(args: argparse.Namespace) -> ModelConfig:
    return _model_config_for_name(args, args.model)


def _model_config_for_name(args: argparse.Namespace, model_name: str) -> ModelConfig:
    config = _project_config_from_args(args)
    if config is not None:
        resolved = config.resolve_model(model_name)
        return build_model_config(
            model_name,
            provider=args.provider or resolved.provider,
            base_url=args.base_url or resolved.base_url,
            api_key=resolved.api_key,
        )
    return build_model_config(
        model_name,
        provider=args.provider or "synthetic",
        base_url=args.base_url,
    )


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


def _write_calibration_artifacts(out_dir: Path, data: dict[str, Any]) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "calibration": out_dir / "calibration.json",
        "profile": out_dir / "profile.json",
        "policy": out_dir / "policy.json",
        "spec": out_dir / "spec.json",
        "binding": out_dir / "binding.json",
        "runs": out_dir / "runs.json",
        "report": out_dir / "report.md",
    }
    _write_json(paths["calibration"], data)
    _write_json(paths["profile"], data["profile"])
    _write_json(paths["policy"], data["recommendation"])
    _write_json(paths["spec"], data["spec"])
    _write_json(paths["binding"], data["binding"])
    paths["runs"].write_text(json.dumps(data["runs"], indent=2) + "\n", encoding="utf-8")
    paths["report"].write_text(data["report"] + "\n", encoding="utf-8")
    return {name: str(path) for name, path in paths.items()}


def _write_analysis_sidecars(
    report_path: Path,
    *,
    diagnostics_config: dict[str, Any],
    metrics: dict[str, Any],
    diagnosis: list[dict[str, Any]],
    trace_warnings: list[dict[str, Any]],
    policy_diff: list[dict[str, Any]],
) -> None:
    _write_json(
        report_path.with_suffix(".analysis.json"),
        {
            "diagnostics_config": diagnostics_config,
            "metrics": metrics,
            "trace_warnings": trace_warnings,
            "diagnosis": {"signals": diagnosis},
            "policy_diff": {"changes": policy_diff},
        },
    )
    _write_json(report_path.with_suffix(".metrics.json"), metrics)
    _write_json(
        report_path.with_suffix(".diagnosis.json"),
        {
            "config": diagnostics_config,
            "trace_warnings": trace_warnings,
            "signals": diagnosis,
        },
    )
    _write_json(report_path.with_suffix(".policy-diff.json"), {"changes": policy_diff})


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.path)
    created: list[str] = []
    skipped: list[str] = []
    template_root = files("adaharness.templates")
    for source_name, target_name in INIT_TEMPLATE_FILES:
        target = root / target_name
        if target.exists() and not args.force:
            skipped.append(str(target))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        content = template_root.joinpath(source_name).read_text(encoding="utf-8")
        target.write_text(content, encoding="utf-8")
        created.append(str(target))

    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "path": str(root),
        "purpose": (
            "Starter files for smoke testing AdaHarness. Replace bundled traces with "
            "JSONL events from your own agent runs before using the report for decisions."
        ),
        "created": created,
        "skipped": skipped,
        "example_command": (
            "adaharness analyze "
            f"--traces {root / 'traces' / 'overconstrained_harness.jsonl'} "
            f"--current-policy {root / 'policies' / 'current-policy.json'} "
            f"--diagnostics-config {root / 'diagnostics' / 'default.toml'} "
            f"--out {root / 'reports' / 'harness-drift.md'}"
        ),
    }
    print(json.dumps(data, indent=2))
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    _run_analysis(
        trace_paths=[Path(path) for path in args.traces],
        current_policy=Path(args.current_policy) if args.current_policy else None,
        diagnostics_config_path=args.diagnostics_config,
        out=Path(args.out) if args.out else None,
    )
    return 0


def _run_analysis(
    *,
    trace_paths: list[Path],
    current_policy: Path | None = None,
    diagnostics_config_path: str | None = None,
    out: Path | None = None,
) -> str:
    events = load_trace_events(trace_paths)
    diagnostics_config = load_diagnostic_config(diagnostics_config_path)
    trace_warnings = validate_trace_events(events)
    metrics = compute_trace_metrics(events)
    signals = diagnose_harness(metrics, config=diagnostics_config)
    changes = recommend_policy_changes(
        signals,
        current_policy=_load_policy_dict(current_policy) if current_policy else None,
    )
    report = render_analysis_report(
        metrics=metrics,
        signals=signals,
        changes=changes,
        trace_warnings=trace_warnings,
    )
    diagnostics_config_data = diagnostics_config.to_dict()
    metrics_data = metrics.to_dict()
    trace_warnings_data = [warning.to_dict() for warning in trace_warnings]
    diagnosis_data = [signal.to_dict() for signal in signals]
    policy_diff_data = [change.to_dict() for change in changes]
    if out:
        report_path = out
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report + "\n", encoding="utf-8")
        _write_analysis_sidecars(
            report_path,
            diagnostics_config=diagnostics_config_data,
            metrics=metrics_data,
            diagnosis=diagnosis_data,
            trace_warnings=trace_warnings_data,
            policy_diff=policy_diff_data,
        )
    else:
        print(report)
    return report


def cmd_capture(args: argparse.Namespace) -> int:
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    tasks = load_capture_tasks(Path(args.tasks))
    out_path = Path(args.out)
    summary = capture_command_runs(
        tasks=tasks,
        command=command,
        out_path=out_path,
        model=args.model,
        policy=args.policy,
        timeout=args.timeout,
        stdin_field=args.stdin_field,
        append=args.append,
        include_output=args.include_output,
    )
    data = summary.to_dict()
    if args.analyze_out:
        _run_analysis(
            trace_paths=[out_path],
            current_policy=Path(args.current_policy) if args.current_policy else None,
            diagnostics_config_path=args.diagnostics_config,
            out=Path(args.analyze_out),
        )
        data["analysis_report"] = args.analyze_out
    print(json.dumps(data, indent=2))
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    config = load_config(args.config, env_file=args.env_file)
    taskset_value = args.taskset or config.project.taskset or config.defaults.taskset
    if not taskset_value:
        raise ValueError("calibrate requires [project].taskset, [defaults].taskset, or --taskset")
    adapter = _load_project_adapter(config, adapter_path=args.adapter)
    tasks = load_taskset(_resolve_config_path(config, taskset_value))
    risk = args.risk or config.defaults.risk
    budget = args.budget or config.defaults.budget
    result = calibrate_project(adapter, tasks, risk=risk, budget=budget)
    data = result.to_dict()
    out_dir_value = args.out_dir or config.project.artifact_dir
    out_dir = _resolve_config_path(config, out_dir_value)
    artifacts = _write_calibration_artifacts(out_dir, data)
    summary = {
        "project": result.profile.project_name,
        "task_count": result.profile.task_count,
        "success_rate": result.profile.success_rate,
        "artifact_dir": str(out_dir),
        "artifacts": artifacts,
    }
    print(json.dumps(summary, indent=2))
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    config = _project_config_from_args(args)
    taskset_value = args.taskset or (config.defaults.taskset if config else None)
    taskset = Path(taskset_value) if taskset_value else None
    profile = run_profiler(_model_config_from_args(args), taskset=taskset)
    data = profile.to_dict()
    if args.out:
        _write_json(Path(args.out), data)
    print(json.dumps(data, indent=2))
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    config = _project_config_from_args(args)
    profile = _load_profile(Path(args.profile))
    risk = args.risk or (config.defaults.risk if config else "medium")
    budget = args.budget or (config.defaults.budget if config else "standard")
    recommendation = recommend_policy(profile, risk=risk, budget=budget)
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
        model_config = _model_config_for_name(args, model_name)
        profile = _load_profile(Path(args.profile)) if args.profile else run_profiler(model_config)
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
    config = _project_config_from_args(args)
    from_profile = _load_profile(Path(args.from_profile))
    to_profile = _load_profile(Path(args.to_profile))
    from_policy, _ = _load_policy(Path(args.from_policy))
    risk = args.risk or (config.defaults.risk if config else "medium")
    budget = args.budget or (config.defaults.budget if config else "standard")
    report = build_migration_report(
        from_profile=from_profile,
        to_profile=to_profile,
        from_policy=from_policy,
        risk=risk,
        budget=budget,
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


def cmd_import_trace(args: argparse.Namespace) -> int:
    trace = import_external_trace(Path(args.source))
    data = trace.to_dict()
    if args.out:
        _write_json(Path(args.out), data)
    print(json.dumps(data, indent=2))
    return 0


def cmd_config_inspect(args: argparse.Namespace) -> int:
    config = load_config(args.config, env_file=args.env_file)
    print(json.dumps(config.to_dict(), indent=2))
    return 0


def cmd_config_validate(args: argparse.Namespace) -> int:
    config = load_config(args.config, env_file=args.env_file)
    resolved_models = {
        model_name: config.resolve_model(model_name)
        for model_name in config.models
    }
    data = {
        "valid": True,
        "model_count": len(resolved_models),
        "provider_count": len(config.providers),
        "project_adapter": config.project.adapter,
        "project_taskset": config.project.taskset,
        "models": sorted(resolved_models),
    }
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

    init = subparsers.add_parser("init", help="Create starter AdaHarness project files")
    init.add_argument("--path", default=".adaharness")
    init.add_argument("--force", action="store_true", help="Overwrite existing starter files")
    init.set_defaults(func=cmd_init)

    analyze = subparsers.add_parser("analyze", help="Analyze exported agent traces")
    analyze.add_argument("--traces", nargs="+", required=True)
    analyze.add_argument("--current-policy")
    analyze.add_argument("--diagnostics-config", help="Optional TOML file with diagnostic thresholds")
    analyze.add_argument("--out")
    analyze.set_defaults(func=cmd_analyze)

    capture = subparsers.add_parser(
        "capture",
        help="Run task cases through a command and write AdaHarness traces",
    )
    capture.add_argument("--tasks", required=True, help="JSON or JSONL task file")
    capture.add_argument("--out", default=".adaharness/traces/run.jsonl")
    capture.add_argument("--model")
    capture.add_argument("--policy")
    capture.add_argument("--timeout", type=float, default=60.0)
    capture.add_argument("--stdin-field", help="Task field to pass to command stdin")
    capture.add_argument("--append", action="store_true")
    capture.add_argument("--include-output", action="store_true")
    capture.add_argument("--analyze-out", help="Optional report path to analyze captured traces")
    capture.add_argument("--current-policy", help="Optional current policy for --analyze-out")
    capture.add_argument("--diagnostics-config", help="Optional TOML thresholds for --analyze-out")
    capture.add_argument("command", nargs=argparse.REMAINDER, help="Command after --, supports {task_field}")
    capture.set_defaults(func=cmd_capture)

    calibrate = subparsers.add_parser(
        "calibrate",
        help="Experimental: calibrate controls through a host project adapter",
    )
    calibrate.add_argument("--config", required=True)
    calibrate.add_argument("--env-file")
    calibrate.add_argument("--adapter")
    calibrate.add_argument("--taskset")
    calibrate.add_argument("--risk", choices=RISK_LEVELS)
    calibrate.add_argument("--budget", choices=BUDGET_LEVELS)
    calibrate.add_argument("--out-dir")
    calibrate.set_defaults(func=cmd_calibrate)

    profile = subparsers.add_parser("profile", help="Lab: run deterministic model profiler")
    profile.add_argument("--model", required=True)
    profile.add_argument("--config")
    profile.add_argument("--env-file")
    profile.add_argument("--provider", choices=SUPPORTED_PROVIDERS)
    profile.add_argument("--base-url")
    profile.add_argument("--taskset")
    profile.add_argument("--out")
    profile.set_defaults(func=cmd_profile)

    recommend = subparsers.add_parser("recommend", help="Lab: recommend a harness policy from a profile")
    recommend.add_argument("--config")
    recommend.add_argument("--env-file")
    recommend.add_argument("--profile", required=True)
    recommend.add_argument("--risk", choices=RISK_LEVELS)
    recommend.add_argument("--budget", choices=BUDGET_LEVELS)
    recommend.add_argument("--out")
    recommend.set_defaults(func=cmd_recommend)

    assemble = subparsers.add_parser("assemble", help="Experimental: compile a policy into a harness spec")
    assemble.add_argument("--policy", required=True)
    assemble.add_argument("--name", default="compiled_harness")
    assemble.add_argument("--out")
    assemble.set_defaults(func=cmd_assemble)

    compare = subparsers.add_parser("compare", help="Lab: compare harness presets")
    compare.add_argument("--model")
    compare.add_argument("--models")
    compare.add_argument("--config")
    compare.add_argument("--env-file")
    compare.add_argument("--provider", choices=SUPPORTED_PROVIDERS)
    compare.add_argument("--base-url")
    compare.add_argument("--harnesses")
    compare.add_argument("--profile")
    compare.add_argument("--taskset", required=True)
    compare.add_argument("--out")
    compare.set_defaults(func=cmd_compare)

    run = subparsers.add_parser("run", help="Experimental: run a task with a compiled harness spec")
    run.add_argument("--harness-spec", required=True)
    run.add_argument("--task", required=True)
    run.add_argument("--model", required=True)
    run.add_argument("--config")
    run.add_argument("--env-file")
    run.add_argument("--provider", choices=SUPPORTED_PROVIDERS)
    run.add_argument("--base-url")
    run.add_argument("--live", action="store_true")
    run.add_argument("--out")
    run.set_defaults(func=cmd_run)

    migrate = subparsers.add_parser("migrate", help="Lab: compare current and recommended harness policy")
    migrate.add_argument("--config")
    migrate.add_argument("--env-file")
    migrate.add_argument("--from-profile", required=True)
    migrate.add_argument("--to-profile", required=True)
    migrate.add_argument("--from-policy", required=True)
    migrate.add_argument("--risk", choices=RISK_LEVELS)
    migrate.add_argument("--budget", choices=BUDGET_LEVELS)
    migrate.add_argument("--out")
    migrate.set_defaults(func=cmd_migrate)

    refine = subparsers.add_parser("refine", help="Lab: propose policy updates from run traces")
    refine.add_argument("--policy", required=True)
    refine.add_argument("--trace", required=True)
    refine.add_argument("--name", default="refined_harness")
    refine.add_argument("--out")
    refine.set_defaults(func=cmd_refine)

    import_trace = subparsers.add_parser("import-trace", help="Normalize an external trace")
    import_trace.add_argument("--source", required=True)
    import_trace.add_argument("--out")
    import_trace.set_defaults(func=cmd_import_trace)

    config = subparsers.add_parser("config", help="Experimental: inspect or validate project configuration")
    config_subparsers = config.add_subparsers(dest="config_command", required=True)

    inspect_config = config_subparsers.add_parser("inspect", help="Print resolved configuration")
    inspect_config.add_argument("--config", required=True)
    inspect_config.add_argument("--env-file")
    inspect_config.set_defaults(func=cmd_config_inspect)

    validate_config = config_subparsers.add_parser("validate", help="Validate project configuration")
    validate_config.add_argument("--config", required=True)
    validate_config.add_argument("--env-file")
    validate_config.set_defaults(func=cmd_config_validate)

    report = subparsers.add_parser("report", help="Lab: render a compare run as Markdown")
    report.add_argument("run")
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
