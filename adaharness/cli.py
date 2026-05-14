from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from adaharness.api import analyze_traces


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_analysis_sidecars(report_path: Path, data: dict[str, Any]) -> None:
    _write_json(
        report_path.with_suffix(".analysis.json"),
        {
            "diagnostics_config": data["diagnostics_config"],
            "metrics": data["metrics"],
            "fit_verdict": data["fit_verdict"],
            "trace_warnings": data["trace_warnings"],
            "diagnosis": data["diagnosis"],
            "policy_diff": data["policy_diff"],
            "group_by": data["group_by"],
            "groups": data["groups"],
        },
    )
    metrics_data: dict[str, Any] = data["metrics"]
    if data["groups"]:
        metrics_data = {
            "aggregate": data["metrics"],
            "groups": [
                {"group": group["group"], "metrics": group["metrics"]}
                for group in data["groups"]
            ],
        }
    _write_json(report_path.with_suffix(".metrics.json"), metrics_data)
    _write_json(
        report_path.with_suffix(".diagnosis.json"),
        {
            "config": data["diagnostics_config"],
            "fit_verdict": data["fit_verdict"],
            "trace_warnings": data["trace_warnings"],
            "signals": data["diagnosis"]["signals"],
            "group_by": data["group_by"],
            "groups": [
                {
                    "group": group["group"],
                    "fit_verdict": group["fit_verdict"],
                    "trace_warnings": group["trace_warnings"],
                    "signals": group["diagnosis"]["signals"],
                }
                for group in data["groups"]
            ],
        },
    )
    policy_diff_data: dict[str, Any] = data["policy_diff"]
    if data["groups"]:
        policy_diff_data = {
            "aggregate": data["policy_diff"],
            "groups": [
                {"group": group["group"], "policy_diff": group["policy_diff"]}
                for group in data["groups"]
            ],
        }
    _write_json(report_path.with_suffix(".policy-diff.json"), policy_diff_data)


def _run_analysis(
    *,
    trace_paths: list[Path],
    current_policy: Path | None = None,
    diagnostics_config_path: str | None = None,
    out: Path | None = None,
    group_by: str | None = None,
) -> str:
    data = analyze_traces(
        trace_paths,
        current_policy=current_policy,
        diagnostics_config=diagnostics_config_path,
        group_by=group_by,
    )
    report = str(data["report"])
    if out:
        report_path = out
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report + "\n", encoding="utf-8")
        _write_analysis_sidecars(report_path, data)
    else:
        print(report)
    return report


def cmd_analyze(args: argparse.Namespace) -> int:
    _run_analysis(
        trace_paths=[Path(path) for path in args.traces],
        current_policy=Path(args.current_policy) if args.current_policy else None,
        diagnostics_config_path=args.diagnostics_config,
        out=Path(args.out) if args.out else None,
        group_by=args.group_by,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="adaharness",
        description="Analyze exported agent traces and recommend harness policy diffs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze exported agent traces")
    analyze.add_argument("--traces", nargs="+", required=True)
    analyze.add_argument("--current-policy")
    analyze.add_argument("--diagnostics-config", help="Optional TOML file with diagnostic thresholds")
    analyze.add_argument("--group-by", help="Comma-separated dimensions: model, policy, task_type")
    analyze.add_argument("--out")
    analyze.set_defaults(func=cmd_analyze)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
