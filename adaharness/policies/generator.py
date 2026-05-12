from __future__ import annotations

from dataclasses import replace

from adaharness.policies.artifacts import PolicyRecommendation
from adaharness.policies.presets import LIGHT_POLICY, STRONG_POLICY, STRUCTURED_POLICY
from adaharness.policies.schema import (
    BUDGET_LEVELS,
    RISK_LEVELS,
    BudgetLevel,
    HarnessPolicy,
    RiskLevel,
)
from adaharness.profiler.profile_schema import ModelProfile


def recommend_policy(
    profile: ModelProfile,
    *,
    risk: RiskLevel = "medium",
    budget: BudgetLevel = "standard",
) -> PolicyRecommendation:
    """Generate a reusable policy artifact from model capability evidence."""
    _validate_inputs(risk, budget)
    policy = _base_policy_for_profile(profile)
    rationale = [_base_rationale(profile)]
    policy = _apply_risk(policy, risk, rationale)
    policy = _apply_budget(policy, budget, risk, rationale)
    return PolicyRecommendation(
        model_name=profile.model_name,
        capability_average=profile.capability_average,
        risk=risk,
        budget=budget,
        policy=policy,
        rationale=tuple(rationale),
        profile_schema_version=profile.schema_version,
    )


def generate_policy(
    profile: ModelProfile,
    *,
    risk: RiskLevel = "medium",
    budget: BudgetLevel = "standard",
) -> HarnessPolicy:
    """Choose a minimal effective harness policy from a model profile."""
    return recommend_policy(profile, risk=risk, budget=budget).policy


def _base_policy_for_profile(profile: ModelProfile) -> HarnessPolicy:
    average = profile.capability_average

    if average < 0.45:
        return STRONG_POLICY

    if average < 0.75:
        return STRUCTURED_POLICY

    return LIGHT_POLICY


def _base_rationale(profile: ModelProfile) -> str:
    average = profile.capability_average
    if average < 0.45:
        return "Capability average is weak, so the base policy starts with strong controls."
    if average < 0.75:
        return "Capability average is mixed, so the base policy starts with structured controls."
    return "Capability average is strong, so the base policy starts with light controls."


def _apply_risk(
    policy: HarnessPolicy,
    risk: RiskLevel,
    rationale: list[str],
) -> HarnessPolicy:
    if risk == "medium":
        return policy

    if risk == "high":
        rationale.append("High risk strengthens verification, tool gatekeeping, and retry control.")
        return replace(
            policy,
            planning_depth=_raise(policy.planning_depth, ("none", "light", "explicit", "strict")),
            tool_gatekeeping=_raise(policy.tool_gatekeeping, ("none", "moderate", "strict")),
            verifier_strength=_raise(policy.verifier_strength, ("none", "selective", "always")),
            retry_policy=_raise(policy.retry_policy, ("none", "bounded", "aggressive")),
            autonomy_budget=_lower(policy.autonomy_budget, ("small", "medium", "large")),
        )

    rationale.append("Low risk allows lighter verification, retry, and tool gatekeeping.")
    return replace(
        policy,
        tool_gatekeeping=_lower(policy.tool_gatekeeping, ("none", "moderate", "strict")),
        verifier_strength=_lower(policy.verifier_strength, ("none", "selective", "always")),
        retry_policy=_lower(policy.retry_policy, ("none", "bounded", "aggressive")),
    )


def _apply_budget(
    policy: HarnessPolicy,
    budget: BudgetLevel,
    risk: RiskLevel,
    rationale: list[str],
) -> HarnessPolicy:
    if budget == "standard":
        return policy

    if budget == "generous":
        rationale.append("Generous budget permits deeper planning and stronger recovery controls.")
        return replace(
            policy,
            planning_depth=_raise(policy.planning_depth, ("none", "light", "explicit", "strict")),
            retry_policy=_raise(policy.retry_policy, ("none", "bounded", "aggressive")),
        )

    rationale.append("Constrained budget reduces expensive controls while preserving risk floor.")
    verifier_floor = "selective" if risk == "high" else "none"
    gatekeeping_floor = "moderate" if risk == "high" else "none"
    retry_floor = "bounded" if risk == "high" else "none"
    return replace(
        policy,
        planning_depth=_lower(policy.planning_depth, ("none", "light", "explicit", "strict")),
        tool_gatekeeping=_lower(
            policy.tool_gatekeeping,
            ("none", "moderate", "strict"),
            floor=gatekeeping_floor,
        ),
        verifier_strength=_lower(
            policy.verifier_strength,
            ("none", "selective", "always"),
            floor=verifier_floor,
        ),
        retry_policy=_lower(policy.retry_policy, ("none", "bounded", "aggressive"), floor=retry_floor),
        context_policy="summarized" if policy.context_policy == "retrieval_augmented" else policy.context_policy,
    )


def _raise(value: str, order: tuple[str, ...]) -> str:
    index = min(order.index(value) + 1, len(order) - 1)
    return order[index]


def _lower(value: str, order: tuple[str, ...], *, floor: str | None = None) -> str:
    floor_index = order.index(floor) if floor else 0
    index = max(order.index(value) - 1, floor_index)
    return order[index]


def _validate_inputs(risk: RiskLevel, budget: BudgetLevel) -> None:
    if risk not in RISK_LEVELS:
        raise ValueError(f"risk must be one of {RISK_LEVELS}, got {risk!r}")
    if budget not in BUDGET_LEVELS:
        raise ValueError(f"budget must be one of {BUDGET_LEVELS}, got {budget!r}")
