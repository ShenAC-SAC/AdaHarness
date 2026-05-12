from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from adaharness.harnesses.builder import HarnessBuilder
from adaharness.harnesses.modular import ModularHarness
from adaharness.models import ModelConfig, build_model_config
from adaharness.policies.artifacts import PolicyRecommendation
from adaharness.policies.generator import recommend_policy
from adaharness.policies.schema import BudgetLevel, HarnessPolicy, RiskLevel
from adaharness.profiler.profile_schema import ModelProfile
from adaharness.profiler.runner import run_profiler
from adaharness.specs import compile_policy_to_spec
from adaharness.specs.harness_spec import HarnessSpec


def profile_model(
    model: str | ModelConfig,
    *,
    provider: str = "synthetic",
    base_url: str | None = None,
    taskset: str | Path | None = None,
) -> ModelProfile:
    config = build_model_config(model, provider=provider, base_url=base_url) if isinstance(model, str) else model
    taskset_path = Path(taskset) if taskset is not None else None
    return run_profiler(config, taskset=taskset_path)


def recommend_harness_policy(
    profile: ModelProfile,
    *,
    risk: RiskLevel = "medium",
    budget: BudgetLevel = "standard",
) -> PolicyRecommendation:
    return recommend_policy(profile, risk=risk, budget=budget)


def compile_harness_spec(
    policy: HarnessPolicy | PolicyRecommendation,
    *,
    name: str = "compiled_harness",
    metadata: dict[str, Any] | None = None,
) -> HarnessSpec:
    if isinstance(policy, PolicyRecommendation):
        metadata = {
            "recommendation": {
                "model_name": policy.model_name,
                "risk": policy.risk,
                "budget": policy.budget,
                "source": policy.source,
                "schema_version": policy.schema_version,
            },
            **(metadata or {}),
        }
        policy = policy.policy
    return compile_policy_to_spec(policy, name=name, metadata=metadata)


def build_reference_harness(spec: HarnessSpec) -> ModularHarness:
    return HarnessBuilder().build(spec)


def load_profile(path: str | Path) -> ModelProfile:
    return ModelProfile.from_dict(_load_json(Path(path)))


def load_policy(path: str | Path) -> HarnessPolicy:
    data = _load_json(Path(path))
    if "policy" in data:
        return PolicyRecommendation.from_dict(data).policy
    return HarnessPolicy.from_dict(data)


def load_policy_recommendation(path: str | Path) -> PolicyRecommendation:
    return PolicyRecommendation.from_dict(_load_json(Path(path)))


def load_spec(path: str | Path) -> HarnessSpec:
    return HarnessSpec.from_dict(_load_json(Path(path)))


def save_artifact(path: str | Path, artifact: Any) -> None:
    data = artifact.to_dict() if hasattr(artifact, "to_dict") else artifact
    _write_json(Path(path), data)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
