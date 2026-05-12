from __future__ import annotations

from adaharness.policies.presets import LIGHT_POLICY, STRONG_POLICY, STRUCTURED_POLICY
from adaharness.policies.schema import HarnessPolicy
from adaharness.profiler.profile_schema import ModelProfile


def generate_policy(profile: ModelProfile) -> HarnessPolicy:
    """Choose a minimal effective harness policy from a model profile."""
    average = profile.capability_average

    if average < 0.45:
        return STRONG_POLICY

    if average < 0.75:
        return STRUCTURED_POLICY

    return LIGHT_POLICY
