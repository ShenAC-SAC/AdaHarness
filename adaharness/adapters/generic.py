from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from adaharness.adapters.binding import AdapterCapabilities, RuntimeBinding
from adaharness.specs.harness_spec import ControllerSpec, HarnessSpec


_CONTROLLER_REQUIREMENTS = {
    "tracing": ("supports_trace_export", "trace_export"),
    "budget": ("supports_pre_model_hook", "before_model_call"),
    "tool_execution": ("supports_tool_execution", "tool_execution"),
    "planner": ("supports_pre_model_hook", "before_model_call"),
    "context": ("supports_pre_model_hook", "before_model_call"),
    "tool_control": ("supports_tool_interception", "before_tool_call"),
    "verifier": ("supports_post_model_hook", "after_model_call"),
    "retry": ("supports_retry_loop", "on_failure"),
    "recovery": ("supports_retry_loop", "on_failure"),
    "delegation": ("supports_subagents", "subagent_route"),
    "autonomy": ("supports_pre_model_hook", "before_model_call"),
}


@dataclass(frozen=True)
class GenericRuntimeAdapter:
    name: str = "generic"
    capabilities: AdapterCapabilities = field(default_factory=AdapterCapabilities)

    def inspect(self, target: Any | None = None) -> AdapterCapabilities:
        return self.capabilities

    def bind(self, spec: HarnessSpec, target: Any | None = None) -> RuntimeBinding:
        capabilities = self.inspect(target)
        bindings: dict[str, Any] = {}
        unsupported_controllers: list[str] = []
        unsupported_modules: list[str] = []
        warnings: list[str] = []
        for controller in spec.controllers:
            if not controller.enabled:
                continue
            requirement, hook = _CONTROLLER_REQUIREMENTS.get(controller.name, ("", ""))
            if not requirement:
                unsupported_controllers.append(controller.name)
                warnings.append(f"No generic binding rule for controller {controller.name}.")
                continue
            if not getattr(capabilities, requirement):
                unsupported_controllers.append(controller.name)
                warnings.append(f"Controller {controller.name} requires {requirement}.")
                continue
            bindings[controller.name] = _binding_for(controller, hook, spec)
        unsupported_modules = _unsupported_legacy_modules(spec, bindings)
        return RuntimeBinding(
            runtime=self.name,
            spec_name=spec.name,
            enabled_features=tuple(bindings),
            bindings=bindings,
            unsupported_controllers=tuple(unsupported_controllers),
            unsupported_modules=tuple(unsupported_modules),
            warnings=tuple(warnings),
        )


def bind_runtime(
    spec: HarnessSpec,
    *,
    capabilities: AdapterCapabilities | None = None,
    runtime: str = "generic",
) -> RuntimeBinding:
    adapter = GenericRuntimeAdapter(name=runtime, capabilities=capabilities or AdapterCapabilities())
    return adapter.bind(spec)


def _binding_for(controller: ControllerSpec, hook: str, spec: HarnessSpec) -> dict[str, Any]:
    legacy_module = _legacy_module_for_controller(controller.name)
    module = spec.get_module(legacy_module) if legacy_module else None
    return {
        "hook": hook,
        "controller": controller.name,
        "level": controller.level,
        "mode": controller.mode,
        "authority": controller.authority,
        "triggers": list(controller.triggers),
        "budget": controller.budget,
        "escalation": controller.escalation,
        "config": controller.config,
        "legacy_module": module.name if module else None,
        "legacy_module_config": module.config if module else {},
    }


def _unsupported_legacy_modules(spec: HarnessSpec, bindings: dict[str, Any]) -> list[str]:
    supported_modules = {
        binding["legacy_module"]
        for binding in bindings.values()
        if binding.get("legacy_module")
    }
    return [
        module.name
        for module in spec.modules
        if module.enabled and module.name not in supported_modules and module.name != "tool_executor"
    ]


def _legacy_module_for_controller(controller_name: str) -> str | None:
    return {
        "tracing": "trace",
        "budget": "budget_guard",
        "tool_execution": "tool_executor",
        "planner": "planner",
        "context": "context_manager",
        "tool_control": "tool_gatekeeper",
        "verifier": "verifier",
        "retry": "retry_controller",
        "recovery": "recovery",
        "delegation": "subagent_router",
        "autonomy": "budget_guard",
    }.get(controller_name)
