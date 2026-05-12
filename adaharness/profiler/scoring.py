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
)


def synthetic_profile(model_name: str) -> ModelProfile:
    """Return a deterministic placeholder profile until live profilers are added."""
    return ModelProfile(
        model_name=model_name,
        planning=DEFAULT_PROFILE.planning,
        tool_use=DEFAULT_PROFILE.tool_use,
        instruction_following=DEFAULT_PROFILE.instruction_following,
        self_verification=DEFAULT_PROFILE.self_verification,
        context_management=DEFAULT_PROFILE.context_management,
        recovery=DEFAULT_PROFILE.recovery,
        cost_sensitivity=DEFAULT_PROFILE.cost_sensitivity,
    )
