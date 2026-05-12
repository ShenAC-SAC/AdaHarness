from __future__ import annotations

from adaharness.harnesses.base import Harness
from adaharness.policies.generator import generate_policy
from adaharness.profiler.profile_schema import ModelProfile


def build_adaptive_harness(profile: ModelProfile) -> Harness:
    return Harness(name="adaptive", policy=generate_policy(profile))
