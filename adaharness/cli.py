from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from adaharness.evals.runner import compare_harnesses
from adaharness.evals.task_schema import load_taskset
from adaharness.harnesses import BARE_HARNESS, LIGHT_HARNESS, STRONG_HARNESS, build_adaptive_harness
from adaharness.harnesses.base import Harness
from adaharness.policies.generator import generate_policy
from adaharness.profiler.profile_schema import ModelProfile
from adaharness.profiler.runner import run_profiler


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _load_profile(path: Path) -> ModelProfile:
    return ModelProfile.from_dict(json.loads(path.read_text(encoding="utf-8")))


def cmd_profile(args: argparse.Namespace) -> int:
    profile = run_profiler(args.model)
    data = profile.to_dict()
    if args.out:
        _write_json(Path(args.out), data)
    print(json.dumps(data, indent=2))
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    profile = _load_profile(Path(args.profile))
    policy = generate_policy(profile)
    data = {
        "model_name": profile.model_name,
        "capability_average": profile.capability_average,
        "policy": policy.to_dict(),
    }
    print(json.dumps(data, indent=2))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    profile = run_profiler(args.model)
    if args.profile:
        profile = _load_profile(Path(args.profile))

    tasks = load_taskset(Path(args.taskset))
    harnesses: list[Harness] = [
        BARE_HARNESS,
        LIGHT_HARNESS,
        STRONG_HARNESS,
        build_adaptive_harness(profile),
    ]
    metrics = compare_harnesses(profile, harnesses, tasks)
    data = {
        "model_name": profile.model_name,
        "profile": profile.to_dict(),
        "task_count": len(tasks),
        "results": [item.to_dict() for item in metrics],
    }
    if args.out:
        _write_json(Path(args.out), data)
    print(json.dumps(data, indent=2))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.run).read_text(encoding="utf-8"))
    lines = [
        f"# AdaHarness Report: {data['model_name']}",
        "",
        f"- Task count: {data['task_count']}",
        "",
        "| Harness | Success | Cost | Tax | Lift | MEH Score |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in data["results"]:
        lines.append(
            "| {harness_name} | {success_rate:.2f} | {estimated_cost:.2f} | "
            "{harness_tax:.2f} | {harness_lift:.2f} | "
            "{minimal_effective_harness_score:.2f} |".format(**item)
        )
    print("\n".join(lines))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adaharness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    profile = subparsers.add_parser("profile", help="Run model profiler")
    profile.add_argument("--model", required=True)
    profile.add_argument("--out")
    profile.set_defaults(func=cmd_profile)

    recommend = subparsers.add_parser("recommend", help="Recommend a harness policy")
    recommend.add_argument("--profile", required=True)
    recommend.set_defaults(func=cmd_recommend)

    compare = subparsers.add_parser("compare", help="Compare harness presets")
    compare.add_argument("--model", required=True)
    compare.add_argument("--profile")
    compare.add_argument("--taskset", required=True)
    compare.add_argument("--out")
    compare.set_defaults(func=cmd_compare)

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
