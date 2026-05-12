from __future__ import annotations

from adaharness.models.base import ModelConfig
from adaharness.profiler.profile_schema import ModelProfile
from adaharness.profiler.scoring import synthetic_profile


def run_profiler(model: str | ModelConfig) -> ModelProfile:
    """Run the placeholder profiler.

    The MVP keeps this deterministic so policy selection and reports are easy to
    test before real model adapters are wired in.
    """
    model_name = model.name if isinstance(model, ModelConfig) else model
    return synthetic_profile(model_name)
