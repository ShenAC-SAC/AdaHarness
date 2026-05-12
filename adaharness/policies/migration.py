from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adaharness.policies.generator import recommend_policy
from adaharness.policies.schema import BudgetLevel, HarnessPolicy, RiskLevel
from adaharness.profiler.profile_schema import ModelProfile
from adaharness.specs import compile_policy_to_spec
from adaharness.specs.harness_spec import HarnessSpec


@dataclass(frozen=True)
class MigrationReport:
    from_model: str
    to_model: str
    risk: RiskLevel
    budget: BudgetLevel
    from_policy: HarnessPolicy
    recommended_policy: HarnessPolicy
    from_spec: HarnessSpec
    recommended_spec: HarnessSpec
    policy_diff: tuple[dict[str, Any], ...]
    module_diff: dict[str, Any]
    metrics: dict[str, float]
    recommendation: tuple[str, ...]
    schema_version: str = "0.7"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "from_model": self.from_model,
            "to_model": self.to_model,
            "risk": self.risk,
            "budget": self.budget,
            "from_policy": self.from_policy.to_dict(),
            "recommended_policy": self.recommended_policy.to_dict(),
            "from_spec": self.from_spec.to_dict(),
            "recommended_spec": self.recommended_spec.to_dict(),
            "policy_diff": list(self.policy_diff),
            "module_diff": self.module_diff,
            "metrics": self.metrics,
            "recommendation": list(self.recommendation),
        }


def build_migration_report(
    *,
    from_profile: ModelProfile,
    to_profile: ModelProfile,
    from_policy: HarnessPolicy,
    risk: RiskLevel = "medium",
    budget: BudgetLevel = "standard",
) -> MigrationReport:
    recommendation = recommend_policy(to_profile, risk=risk, budget=budget)
    recommended_policy = recommendation.policy
    from_spec = compile_policy_to_spec(from_policy, name=f"{from_profile.model_name}_current")
    recommended_spec = compile_policy_to_spec(recommended_policy, name=f"{to_profile.model_name}_recommended")
    policy_diff = tuple(diff_policies(from_policy, recommended_policy))
    module_diff = diff_modules(from_spec, recommended_spec)
    metrics = _migration_metrics(from_profile, to_profile, from_spec, recommended_spec, policy_diff)
    return MigrationReport(
        from_model=from_profile.model_name,
        to_model=to_profile.model_name,
        risk=risk,
        budget=budget,
        from_policy=from_policy,
        recommended_policy=recommended_policy,
        from_spec=from_spec,
        recommended_spec=recommended_spec,
        policy_diff=policy_diff,
        module_diff=module_diff,
        metrics=metrics,
        recommendation=_migration_recommendations(metrics, module_diff),
    )


def diff_policies(from_policy: HarnessPolicy, to_policy: HarnessPolicy) -> list[dict[str, Any]]:
    before = from_policy.to_dict()
    after = to_policy.to_dict()
    return [
        {"field": field, "from": before[field], "to": after[field]}
        for field in before
        if before[field] != after[field]
    ]


def diff_modules(from_spec: HarnessSpec, to_spec: HarnessSpec) -> dict[str, Any]:
    before = {module.name: module for module in from_spec.modules}
    after = {module.name: module for module in to_spec.modules}
    names = sorted(set(before) | set(after))
    enabled = []
    disabled = []
    config_changed = []
    for name in names:
        old = before.get(name)
        new = after.get(name)
        if old is None or new is None:
            continue
        if not old.enabled and new.enabled:
            enabled.append(name)
        elif old.enabled and not new.enabled:
            disabled.append(name)
        elif old.enabled and new.enabled and old.config != new.config:
            config_changed.append(
                {
                    "module": name,
                    "from": old.config,
                    "to": new.config,
                }
            )
    return {
        "enabled": enabled,
        "disabled": disabled,
        "config_changed": config_changed,
    }


def _migration_metrics(
    from_profile: ModelProfile,
    to_profile: ModelProfile,
    from_spec: HarnessSpec,
    to_spec: HarnessSpec,
    policy_diff: tuple[dict[str, Any], ...],
) -> dict[str, float]:
    old_control = _control_weight(from_spec)
    new_control = _control_weight(to_spec)
    capability_change = to_profile.capability_average - from_profile.capability_average
    policy_delta = len(policy_diff) + len(set(from_spec.enabled_modules) ^ set(to_spec.enabled_modules))
    return {
        "policy_delta": float(policy_delta),
        "harness_drift_score": min(1.0, policy_delta / 12.0),
        "overconstraint_penalty": max(0.0, capability_change) * max(0.0, old_control - new_control),
        "underconstraint_risk": max(0.0, -capability_change) * max(0.0, new_control - old_control),
    }


def _control_weight(spec: HarnessSpec) -> float:
    enabled = [module for module in spec.modules if module.enabled]
    if not spec.modules:
        return 0.0
    return len(enabled) / len(spec.modules)


def _migration_recommendations(metrics: dict[str, float], module_diff: dict[str, Any]) -> tuple[str, ...]:
    recommendations = []
    if metrics["harness_drift_score"] > 0.4:
        recommendations.append("Review policy and module diffs before migrating.")
    if metrics["overconstraint_penalty"] > 0.0:
        recommendations.append("The old harness may over-constrain the replacement model.")
    if metrics["underconstraint_risk"] > 0.0:
        recommendations.append("The replacement model may need stronger controls than the old harness.")
    if module_diff["enabled"]:
        recommendations.append("Enable newly recommended modules before rollout.")
    if module_diff["disabled"]:
        recommendations.append("Disable modules that no longer justify their harness tax.")
    if not recommendations:
        recommendations.append("The existing harness is close to the recommended policy.")
    return tuple(recommendations)
