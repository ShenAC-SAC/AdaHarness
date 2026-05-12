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
class HarnessSpec:
    """Compiled module assembly plan produced from a HarnessPolicy."""

    name: str
    modules: tuple[ModuleSpec, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "0.3"

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
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def enabled_modules(self) -> tuple[str, ...]:
        return tuple(module.name for module in self.modules if module.enabled)

    @property
    def disabled_modules(self) -> tuple[str, ...]:
        return tuple(module.name for module in self.modules if not module.enabled)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "enabled_modules": list(self.enabled_modules),
            "disabled_modules": list(self.disabled_modules),
            "modules": [module.to_dict() for module in self.modules],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HarnessSpec":
        return cls(
            name=data["name"],
            modules=tuple(ModuleSpec.from_dict(item) for item in data.get("modules", ())),
            metadata=data.get("metadata", {}),
            schema_version=data.get("schema_version", "0.3"),
        )
