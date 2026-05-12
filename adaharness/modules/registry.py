from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from adaharness.modules.base import HarnessModule
from adaharness.modules.budget_guard import BudgetGuardModule
from adaharness.modules.context_manager import ContextManagerModule
from adaharness.modules.planner import PlannerModule
from adaharness.modules.recovery import RecoveryModule
from adaharness.modules.retry_controller import RetryControllerModule
from adaharness.modules.subagent_router import SubagentRouterModule
from adaharness.modules.tool_executor import ToolExecutorModule
from adaharness.modules.tool_gatekeeper import ToolGatekeeperModule
from adaharness.modules.tracing import TraceModule
from adaharness.modules.verifier import VerifierModule
from adaharness.specs.harness_spec import ModuleSpec

ModuleFactory = Callable[[dict[str, Any]], HarnessModule]


def _default_factories() -> dict[str, ModuleFactory]:
    return {
        "trace": TraceModule,
        "budget_guard": BudgetGuardModule,
        "tool_executor": ToolExecutorModule,
        "planner": PlannerModule,
        "context_manager": ContextManagerModule,
        "tool_gatekeeper": ToolGatekeeperModule,
        "verifier": VerifierModule,
        "retry_controller": RetryControllerModule,
        "recovery": RecoveryModule,
        "subagent_router": SubagentRouterModule,
    }


@dataclass(frozen=True)
class ModuleRegistry:
    factories: dict[str, ModuleFactory] = field(default_factory=_default_factories)

    def __post_init__(self) -> None:
        object.__setattr__(self, "factories", dict(self.factories))

    def create(self, spec: ModuleSpec) -> HarnessModule:
        if spec.name not in self.factories:
            supported = ", ".join(sorted(self.factories))
            raise ValueError(f"Unsupported module {spec.name!r}. Expected one of: {supported}")
        return self.factories[spec.name](spec.config)


DEFAULT_MODULE_REGISTRY = ModuleRegistry()
