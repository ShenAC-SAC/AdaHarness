from __future__ import annotations

from adaharness.profiler.profile_schema import ModelProfile


DEFAULT_PROFILE = ModelProfile(
    model_name="example-model",
    planning=0.62,
    tool_use=0.58,
    instruction_following=0.72,
    self_verification=0.54,
    context_management=0.61,
    recovery=0.50,
    cost_sensitivity=0.50,
    delegation=0.50,
)


def synthetic_profile(model_name: str) -> ModelProfile:
    """Return a deterministic placeholder profile until live profilers are added."""
    scores = _synthetic_scores_for_name(model_name)
    return ModelProfile(
        model_name=model_name,
        planning=scores["planning"],
        tool_use=scores["tool_use"],
        instruction_following=scores["instruction_following"],
        self_verification=scores["self_verification"],
        context_management=scores["context_management"],
        recovery=scores["recovery"],
        cost_sensitivity=scores["cost_sensitivity"],
        delegation=scores["delegation"],
    )


def _synthetic_scores_for_name(model_name: str) -> dict[str, float]:
    normalized = model_name.lower()
    if any(marker in normalized for marker in ("small", "weak", "mini")):
        return {
            "planning": 0.38,
            "tool_use": 0.42,
            "instruction_following": 0.52,
            "self_verification": 0.34,
            "context_management": 0.45,
            "recovery": 0.32,
            "cost_sensitivity": 0.44,
            "delegation": 0.36,
        }
    if any(marker in normalized for marker in ("strong", "frontier", "gpt", "claude")):
        return {
            "planning": 0.88,
            "tool_use": 0.84,
            "instruction_following": 0.90,
            "self_verification": 0.82,
            "context_management": 0.86,
            "recovery": 0.80,
            "cost_sensitivity": 0.70,
            "delegation": 0.78,
        }
    return {
        "planning": DEFAULT_PROFILE.planning,
        "tool_use": DEFAULT_PROFILE.tool_use,
        "instruction_following": DEFAULT_PROFILE.instruction_following,
        "self_verification": DEFAULT_PROFILE.self_verification,
        "context_management": DEFAULT_PROFILE.context_management,
        "recovery": DEFAULT_PROFILE.recovery,
        "cost_sensitivity": DEFAULT_PROFILE.cost_sensitivity,
        "delegation": DEFAULT_PROFILE.delegation,
    }
