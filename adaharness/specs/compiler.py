from __future__ import annotations

from typing import Any

from adaharness.policies.schema import HarnessPolicy
from adaharness.specs.harness_spec import ControllerSpec, HarnessSpec, ModuleSpec


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
    controllers = _controllers_for(policy)
    spec_metadata = {
        "source_policy": policy.to_dict(),
        **(metadata or {}),
    }
    return HarnessSpec(
        name=name,
        modules=tuple(modules),
        controllers=tuple(controllers),
        metadata=spec_metadata,
        source_policy=policy.to_dict(),
        requirements=_requirements_for(controllers),
        adapter_hints=_adapter_hints_for(controllers),
    )


def _requirements_for(controllers: list[ControllerSpec]) -> dict[str, bool]:
    enabled = {controller.name for controller in controllers if controller.enabled}
    return {
        "supports_pre_model_hook": bool(enabled & {"planner", "context", "budget", "autonomy"}),
        "supports_post_model_hook": "verifier" in enabled,
        "supports_tool_interception": "tool_control" in enabled,
        "supports_tool_execution": "tool_execution" in enabled,
        "supports_retry_loop": bool(enabled & {"retry", "recovery"}),
        "supports_subagents": "delegation" in enabled,
        "supports_trace_export": "tracing" in enabled,
    }


def _adapter_hints_for(controllers: list[ControllerSpec]) -> dict[str, Any]:
    hooks = []
    enabled = {controller.name for controller in controllers if controller.enabled}
    if enabled & {"planner", "context", "budget", "autonomy"}:
        hooks.append("before_model_call")
    if "verifier" in enabled:
        hooks.append("after_model_call")
    if "tool_control" in enabled:
        hooks.append("before_tool_call")
    if "tool_execution" in enabled:
        hooks.append("tool_execution")
    if enabled & {"retry", "recovery"}:
        hooks.append("on_retry")
    if "tracing" in enabled:
        hooks.append("trace_export")
    return {
        "preferred_integration": "middleware",
        "required_hooks": hooks,
    }


def _controllers_for(policy: HarnessPolicy) -> list[ControllerSpec]:
    return [
        _tracing_controller(),
        _budget_controller(policy),
        _tool_execution_controller(),
        _planner_controller(policy),
        _context_controller(policy),
        _tool_control_controller(policy),
        _verifier_controller(policy),
        _retry_controller_spec(policy),
        _recovery_controller(policy),
        _delegation_controller(policy),
        _autonomy_controller(policy),
    ]


def _tracing_controller() -> ControllerSpec:
    return ControllerSpec(
        name="tracing",
        level="full",
        mode="event_log",
        authority="runtime",
        config={"record_events": True, "record_policy": True},
    )


def _budget_controller(policy: HarnessPolicy) -> ControllerSpec:
    limits = _budget_limits(policy)
    return ControllerSpec(
        name="budget",
        level=policy.autonomy_budget,
        mode="guardrail",
        authority="runtime",
        budget=limits,
        config={"enforcement": "bounded"},
    )


def _tool_execution_controller() -> ControllerSpec:
    return ControllerSpec(
        name="tool_execution",
        level="deterministic",
        mode="reference_tools",
        authority="runtime",
        config={"toolset": "deterministic"},
    )


def _planner_controller(policy: HarnessPolicy) -> ControllerSpec:
    level = {
        "none": "off",
        "light": "conditional",
        "explicit": "explicit",
        "strict": "strict",
    }[policy.planning_depth]
    authority = {
        "none": "model_led",
        "light": "model_led",
        "explicit": "shared",
        "strict": "harness_led",
    }[policy.planning_depth]
    budgets = {
        "none": {"max_plan_steps": 0, "max_replans": 0},
        "light": {"max_plan_steps": 4, "max_replans": 1},
        "explicit": {"max_plan_steps": 6, "max_replans": 1},
        "strict": {"max_plan_steps": 8, "max_replans": 2},
    }
    triggers = {
        "none": (),
        "light": ("task_complexity_at_least_medium", "risk_at_least_medium"),
        "explicit": ("before_execution",),
        "strict": ("before_execution", "tool_failure", "verification_failure"),
    }
    return ControllerSpec(
        name="planner",
        enabled=policy.planning_depth != "none",
        level=level,
        mode=level,
        authority=authority,
        triggers=triggers[policy.planning_depth],
        budget=budgets[policy.planning_depth],
        config={"plan_format": "checklist" if policy.planning_depth == "light" else "step_schema"},
        escalation={"on_repeated_failure": "strict"} if policy.planning_depth == "light" else {},
    )


def _context_controller(policy: HarnessPolicy) -> ControllerSpec:
    return ControllerSpec(
        name="context",
        enabled=policy.context_policy != "raw",
        level=policy.context_policy,
        mode=policy.context_policy,
        authority="runtime",
        triggers=("before_model_call",) if policy.context_policy != "raw" else (),
        config={"strategy": policy.context_policy},
    )


def _tool_control_controller(policy: HarnessPolicy) -> ControllerSpec:
    return ControllerSpec(
        name="tool_control",
        enabled=policy.tool_gatekeeping != "none",
        level=policy.tool_gatekeeping if policy.tool_gatekeeping != "none" else "off",
        mode="precheck" if policy.tool_gatekeeping == "moderate" else "pre_and_postcheck",
        authority="runtime",
        triggers=("before_tool_call", "after_tool_call") if policy.tool_gatekeeping == "strict" else ("before_tool_call",),
        config={"strictness": policy.tool_gatekeeping},
        escalation={"on_repeated_tool_failure": "strict"} if policy.tool_gatekeeping == "moderate" else {},
    )


def _verifier_controller(policy: HarnessPolicy) -> ControllerSpec:
    checkpoints = {
        "none": (),
        "selective": ("after_tool_call", "before_final"),
        "always": ("after_plan", "after_tool_call", "before_final"),
    }
    return ControllerSpec(
        name="verifier",
        enabled=policy.verifier_strength != "none",
        level=policy.verifier_strength if policy.verifier_strength != "none" else "off",
        mode="checkpoint",
        authority="runtime",
        triggers=checkpoints[policy.verifier_strength],
        config={"checkpoints": list(checkpoints[policy.verifier_strength])},
        escalation={"on_repeated_failure": "always"} if policy.verifier_strength == "selective" else {},
    )


def _retry_controller_spec(policy: HarnessPolicy) -> ControllerSpec:
    max_retries = {
        "none": 0,
        "bounded": 2,
        "aggressive": 4,
    }
    enabled = policy.retry_policy != "none"
    return ControllerSpec(
        name="retry",
        enabled=enabled,
        level=policy.retry_policy,
        mode="failure_based",
        authority="runtime",
        triggers=("tool_failure", "verification_failure") if enabled else (),
        budget={"max_retries": max_retries[policy.retry_policy]},
        config={"retry_on": ["tool_failure", "verification_failure"] if enabled else []},
        escalation={"after_exhausted_retries": "raise_control_level"} if policy.retry_policy == "aggressive" else {},
    )


def _recovery_controller(policy: HarnessPolicy) -> ControllerSpec:
    enabled = policy.retry_policy != "none" or policy.verifier_strength != "none"
    return ControllerSpec(
        name="recovery",
        enabled=enabled,
        level="guided" if enabled else "off",
        mode="failure_repair",
        authority="runtime",
        triggers=("tool_failure", "format_failure", "verification_failure") if enabled else (),
        config={"recover_from": ["tool_failure", "format_failure", "verification_failure"] if enabled else []},
    )


def _delegation_controller(policy: HarnessPolicy) -> ControllerSpec:
    enabled = policy.subagent_policy != "disabled"
    return ControllerSpec(
        name="delegation",
        enabled=enabled,
        level=policy.subagent_policy,
        mode="router",
        authority="runtime",
        triggers=("complex_subtask",) if enabled else (),
        config={"policy": policy.subagent_policy},
    )


def _autonomy_controller(policy: HarnessPolicy) -> ControllerSpec:
    windows = {
        "small": 1,
        "medium": 3,
        "large": 5,
    }
    return ControllerSpec(
        name="autonomy",
        level=policy.autonomy_budget,
        mode="step_window",
        authority="runtime",
        budget={"max_consecutive_model_steps": windows[policy.autonomy_budget]},
        config={"budget": policy.autonomy_budget},
    )


def _trace_module() -> ModuleSpec:
    return ModuleSpec(
        name="trace",
        config={
            "record_events": True,
            "record_policy": True,
        },
    )


def _budget_guard(policy: HarnessPolicy) -> ModuleSpec:
    limits = _budget_limits(policy)
    return ModuleSpec(
        name="budget_guard",
        config={
            "autonomy_budget": policy.autonomy_budget,
            **limits,
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


def _budget_limits(policy: HarnessPolicy) -> dict[str, int]:
    limits = {
        "small": {"max_steps": 6, "max_tool_calls": 3, "max_retries": 1},
        "medium": {"max_steps": 10, "max_tool_calls": 6, "max_retries": 2},
        "large": {"max_steps": 16, "max_tool_calls": 10, "max_retries": 3},
    }
    return limits[policy.autonomy_budget]
