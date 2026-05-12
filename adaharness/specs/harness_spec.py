from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModuleSpec:
    """Runtime-facing configuration for one harness module."""

    name: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "config", dict(self.config))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModuleSpec":
        return cls(
            name=data["name"],
            enabled=data.get("enabled", True),
            config=data.get("config", {}),
        )


@dataclass(frozen=True)
class ControllerSpec:
    """Runtime-neutral control intent for one harness controller."""

    name: str
    enabled: bool = True
    level: str = "off"
    mode: str = "default"
    authority: str = "runtime"
    triggers: tuple[str, ...] = ()
    config: dict[str, Any] = field(default_factory=dict)
    budget: dict[str, Any] = field(default_factory=dict)
    escalation: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "triggers", tuple(self.triggers))
        object.__setattr__(self, "config", dict(self.config))
        object.__setattr__(self, "budget", dict(self.budget))
        object.__setattr__(self, "escalation", dict(self.escalation))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "level": self.level,
            "mode": self.mode,
            "authority": self.authority,
            "triggers": list(self.triggers),
            "config": self.config,
            "budget": self.budget,
            "escalation": self.escalation,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ControllerSpec":
        return cls(
            name=data["name"],
            enabled=data.get("enabled", True),
            level=data.get("level", "off"),
            mode=data.get("mode", "default"),
            authority=data.get("authority", "runtime"),
            triggers=tuple(data.get("triggers", ())),
            config=data.get("config", {}),
            budget=data.get("budget", {}),
            escalation=data.get("escalation", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class HarnessSpec:
    """Compiled controller plan produced from a HarnessPolicy."""

    name: str
    modules: tuple[ModuleSpec, ...]
    controllers: tuple[ControllerSpec, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    source_policy: dict[str, Any] = field(default_factory=dict)
    requirements: dict[str, bool] = field(default_factory=dict)
    adapter_hints: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "0.5"

    def __post_init__(self) -> None:
        modules = tuple(
            module if isinstance(module, ModuleSpec) else ModuleSpec.from_dict(module)
            for module in self.modules
        )
        object.__setattr__(
            self,
            "modules",
            modules,
        )
        controllers = tuple(
            controller
            if isinstance(controller, ControllerSpec)
            else ControllerSpec.from_dict(controller)
            for controller in self.controllers
        )
        if not controllers:
            controllers = _controllers_from_modules(modules)
        object.__setattr__(self, "controllers", controllers)
        object.__setattr__(self, "metadata", dict(self.metadata))
        object.__setattr__(self, "source_policy", dict(self.source_policy))
        object.__setattr__(self, "requirements", dict(self.requirements))
        object.__setattr__(self, "adapter_hints", dict(self.adapter_hints))

    @property
    def enabled_modules(self) -> tuple[str, ...]:
        return tuple(module.name for module in self.modules if module.enabled)

    @property
    def disabled_modules(self) -> tuple[str, ...]:
        return tuple(module.name for module in self.modules if not module.enabled)

    @property
    def enabled_controllers(self) -> tuple[str, ...]:
        return tuple(controller.name for controller in self.controllers if controller.enabled)

    @property
    def disabled_controllers(self) -> tuple[str, ...]:
        return tuple(controller.name for controller in self.controllers if not controller.enabled)

    def get_module(self, name: str) -> ModuleSpec | None:
        for module in self.modules:
            if module.name == name:
                return module
        return None

    def get_controller(self, name: str) -> ControllerSpec | None:
        for controller in self.controllers:
            if controller.name == name:
                return controller
        return None

    def requires(self, requirement: str) -> bool:
        return self.requirements.get(requirement, False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "source_policy": self.source_policy,
            "requirements": self.requirements,
            "adapter_hints": self.adapter_hints,
            "enabled_controllers": list(self.enabled_controllers),
            "disabled_controllers": list(self.disabled_controllers),
            "controllers": [controller.to_dict() for controller in self.controllers],
            "enabled_modules": list(self.enabled_modules),
            "disabled_modules": list(self.disabled_modules),
            "modules": [module.to_dict() for module in self.modules],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HarnessSpec":
        metadata = data.get("metadata", {})
        return cls(
            name=data["name"],
            modules=tuple(ModuleSpec.from_dict(item) for item in data.get("modules", ())),
            controllers=tuple(ControllerSpec.from_dict(item) for item in data.get("controllers", ())),
            metadata=metadata,
            source_policy=data.get("source_policy", metadata.get("source_policy", {})),
            requirements=data.get("requirements", {}),
            adapter_hints=data.get("adapter_hints", {}),
            schema_version=data.get("schema_version", "0.3"),
        )


_MODULE_CONTROLLER_NAMES = {
    "trace": "tracing",
    "budget_guard": "budget",
    "tool_executor": "tool_execution",
    "planner": "planner",
    "context_manager": "context",
    "tool_gatekeeper": "tool_control",
    "verifier": "verifier",
    "retry_controller": "retry",
    "recovery": "recovery",
    "subagent_router": "delegation",
}


def _controllers_from_modules(modules: tuple[ModuleSpec, ...]) -> tuple[ControllerSpec, ...]:
    controllers = []
    for module in modules:
        controllers.append(
            ControllerSpec(
                name=_MODULE_CONTROLLER_NAMES.get(module.name, module.name),
                enabled=module.enabled,
                level=_legacy_level_for_module(module),
                mode="legacy_module",
                authority="runtime",
                config={"module": module.name, **module.config},
            )
        )
    return tuple(controllers)


def _legacy_level_for_module(module: ModuleSpec) -> str:
    for key in ("depth", "strength", "policy", "strictness", "mode", "autonomy_budget"):
        if key in module.config:
            return str(module.config[key])
    return "enabled" if module.enabled else "off"
