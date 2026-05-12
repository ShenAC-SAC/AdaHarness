from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

from adaharness.evals.runner import compare_harness_runs
from adaharness.evals.task_schema import EvalTask
from adaharness.harnesses.base import Harness
from adaharness.policies.generator import generate_policy
from adaharness.policies.schema import HarnessPolicy
from adaharness.profiler.profile_schema import ModelProfile


@dataclass(frozen=True)
class PolicyProposal:
    policy: HarnessPolicy
    rationale: str = ""
    source: str = "fixture"

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy.to_dict(),
            "rationale": self.rationale,
            "source": self.source,
        }


def load_policy_proposal(path: Path) -> PolicyProposal:
    data = json.loads(path.read_text(encoding="utf-8"))
    return PolicyProposal(
        policy=HarnessPolicy.from_dict(data["policy"]),
        rationale=data.get("rationale", ""),
        source=data.get("source", "fixture"),
    )


def compare_policy_proposal(
    profile: ModelProfile,
    proposal: PolicyProposal,
    tasks: list[EvalTask],
) -> dict[str, Any]:
    rule_policy = generate_policy(profile)
    harnesses = [
        Harness(name="rule", policy=rule_policy),
        Harness(name="proposal", policy=proposal.policy),
    ]
    metrics, runs = compare_harness_runs(profile, harnesses, tasks, baseline_name="rule")
    return {
        "model_name": profile.model_name,
        "proposal": proposal.to_dict(),
        "rule_policy": rule_policy.to_dict(),
        "results": [metric.to_dict() for metric in metrics],
        "runs": [run.to_dict() for run in runs],
    }
