from __future__ import annotations

from typing import Any

from adaharness.policies.schema import HarnessPolicy
from adaharness.specs.harness_spec import HarnessSpec, ModuleSpec


def compile_policy_to_spec(
    policy: HarnessPolicy,
    *,
    name: str = "compiled_harness",
    metadata: dict[str, Any] | None = None,
) -> HarnessSpec:
    """Compile high-level policy into concrete module configuration."""
    modules = [
        _trace_module(),
        _budget_guard(policy),
        _tool_executor(),
        _planner(policy),
        _context_manager(policy),
        _tool_gatekeeper(policy),
        _verifier(policy),
        _retry_controller(policy),
        _recovery(policy),
        _subagent_router(policy),
    ]
    spec_metadata = {
        "source_policy": policy.to_dict(),
        **(metadata or {}),
    }
    return HarnessSpec(name=name, modules=tuple(modules), metadata=spec_metadata)


def _trace_module() -> ModuleSpec:
    return ModuleSpec(
        name="trace",
        config={
            "record_events": True,
            "record_policy": True,
        },
    )


def _budget_guard(policy: HarnessPolicy) -> ModuleSpec:
    limits = {
        "small": {"max_steps": 6, "max_tool_calls": 3, "max_retries": 1},
        "medium": {"max_steps": 10, "max_tool_calls": 6, "max_retries": 2},
        "large": {"max_steps": 16, "max_tool_calls": 10, "max_retries": 3},
    }
    return ModuleSpec(
        name="budget_guard",
        config={
            "autonomy_budget": policy.autonomy_budget,
            **limits[policy.autonomy_budget],
        },
    )


def _tool_executor() -> ModuleSpec:
    return ModuleSpec(
        name="tool_executor",
        config={
            "mode": "deterministic",
        },
    )


def _planner(policy: HarnessPolicy) -> ModuleSpec:
    enabled = policy.planning_depth != "none"
    max_steps = {
        "none": 0,
        "light": 3,
        "explicit": 6,
        "strict": 8,
    }
    return ModuleSpec(
        name="planner",
        enabled=enabled,
        config={
            "depth": policy.planning_depth,
            "max_plan_steps": max_steps[policy.planning_depth],
        },
    )


def _context_manager(policy: HarnessPolicy) -> ModuleSpec:
    enabled = policy.context_policy != "raw"
    return ModuleSpec(
        name="context_manager",
        enabled=enabled,
        config={
            "mode": policy.context_policy,
        },
    )


def _tool_gatekeeper(policy: HarnessPolicy) -> ModuleSpec:
    enabled = policy.tool_gatekeeping != "none"
    return ModuleSpec(
        name="tool_gatekeeper",
        enabled=enabled,
        config={
            "strictness": policy.tool_gatekeeping,
        },
    )


def _verifier(policy: HarnessPolicy) -> ModuleSpec:
    enabled = policy.verifier_strength != "none"
    checkpoints = {
        "none": [],
        "selective": ["after_tool_call", "before_final"],
        "always": ["after_plan", "after_tool_call", "before_final"],
    }
    return ModuleSpec(
        name="verifier",
        enabled=enabled,
        config={
            "strength": policy.verifier_strength,
            "checkpoints": checkpoints[policy.verifier_strength],
        },
    )


def _retry_controller(policy: HarnessPolicy) -> ModuleSpec:
    enabled = policy.retry_policy != "none"
    max_retries = {
        "none": 0,
        "bounded": 2,
        "aggressive": 4,
    }
    return ModuleSpec(
        name="retry_controller",
        enabled=enabled,
        config={
            "policy": policy.retry_policy,
            "max_retries": max_retries[policy.retry_policy],
            "retry_on": ["tool_failure", "verification_failure"] if enabled else [],
        },
    )


def _recovery(policy: HarnessPolicy) -> ModuleSpec:
    enabled = policy.retry_policy != "none" or policy.verifier_strength != "none"
    return ModuleSpec(
        name="recovery",
        enabled=enabled,
        config={
            "recover_from": ["tool_failure", "format_failure", "verification_failure"] if enabled else [],
        },
    )


def _subagent_router(policy: HarnessPolicy) -> ModuleSpec:
    enabled = policy.subagent_policy != "disabled"
    return ModuleSpec(
        name="subagent_router",
        enabled=enabled,
        config={
            "policy": policy.subagent_policy,
        },
    )
