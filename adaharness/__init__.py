"""Model-aware harness compiler for LLM agents."""

from adaharness.api import (
    bind_harness_spec,
    build_reference_harness,
    compile_harness_spec,
    load_policy,
    load_policy_recommendation,
    load_profile,
    load_project_config,
    load_spec,
    profile_model,
    recommend_harness_policy,
    save_artifact,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "build_reference_harness",
    "bind_harness_spec",
    "compile_harness_spec",
    "load_policy",
    "load_policy_recommendation",
    "load_profile",
    "load_project_config",
    "load_spec",
    "profile_model",
    "recommend_harness_policy",
    "save_artifact",
]
