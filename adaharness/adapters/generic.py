from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from adaharness.adapters.binding import AdapterCapabilities, RuntimeBinding
from adaharness.specs.harness_spec import HarnessSpec, ModuleSpec


_MODULE_REQUIREMENTS = {
    "trace": ("supports_trace_export", "trace_export"),
    "budget_guard": ("supports_pre_model_hook", "before_model_call"),
    "tool_executor": ("supports_tool_execution", "tool_execution"),
    "planner": ("supports_pre_model_hook", "before_model_call"),
    "context_manager": ("supports_pre_model_hook", "before_model_call"),
    "tool_gatekeeper": ("supports_tool_interception", "before_tool_call"),
    "verifier": ("supports_post_model_hook", "after_model_call"),
    "retry_controller": ("supports_retry_loop", "on_retry"),
    "recovery": ("supports_retry_loop", "on_retry"),
    "subagent_router": ("supports_subagents", "subagent_route"),
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
        unsupported: list[str] = []
        warnings: list[str] = []
        for module in spec.modules:
            if not module.enabled:
                continue
            requirement, hook = _MODULE_REQUIREMENTS.get(module.name, ("", ""))
            if not requirement:
                unsupported.append(module.name)
                warnings.append(f"No generic binding rule for {module.name}.")
                continue
            if not getattr(capabilities, requirement):
                unsupported.append(module.name)
                warnings.append(f"{module.name} requires {requirement}.")
                continue
            bindings[module.name] = _binding_for(module, hook)
        return RuntimeBinding(
            runtime=self.name,
            spec_name=spec.name,
            enabled_features=tuple(bindings),
            bindings=bindings,
            unsupported_modules=tuple(unsupported),
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


def _binding_for(module: ModuleSpec, hook: str) -> dict[str, Any]:
    return {
        "hook": hook,
        "module": module.name,
        "config": module.config,
    }
