from __future__ import annotations

from adaharness.profiler.profile_schema import ModelProfile
from adaharness.profiler.scoring import synthetic_profile


def run_profiler(model_name: str) -> ModelProfile:
    """Run the placeholder profiler.

    The MVP keeps this deterministic so policy selection and reports are easy to
    test before real model adapters are wired in.
    """
    return synthetic_profile(model_name)
