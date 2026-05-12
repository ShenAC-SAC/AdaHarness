from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AdapterCapabilities:
    supports_pre_model_hook: bool = False
    supports_post_model_hook: bool = False
    supports_tool_interception: bool = False
    supports_tool_execution: bool = False
    supports_retry_loop: bool = False
    supports_subagents: bool = False
    supports_trace_export: bool = False

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeBinding:
    runtime: str
    spec_name: str
    enabled_features: tuple[str, ...]
    bindings: dict[str, Any] = field(default_factory=dict)
    unsupported_controllers: tuple[str, ...] = ()
    unsupported_modules: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    schema_version: str = "0.2"

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled_features", tuple(self.enabled_features))
        object.__setattr__(self, "bindings", dict(self.bindings))
        object.__setattr__(self, "unsupported_controllers", tuple(self.unsupported_controllers))
        object.__setattr__(self, "unsupported_modules", tuple(self.unsupported_modules))
        object.__setattr__(self, "warnings", tuple(self.warnings))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "runtime": self.runtime,
            "spec_name": self.spec_name,
            "enabled_features": list(self.enabled_features),
            "bindings": self.bindings,
            "unsupported_controllers": list(self.unsupported_controllers),
            "unsupported_modules": list(self.unsupported_modules),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuntimeBinding":
        return cls(
            runtime=data["runtime"],
            spec_name=data["spec_name"],
            enabled_features=tuple(data.get("enabled_features", ())),
            bindings=data.get("bindings", {}),
            unsupported_controllers=tuple(data.get("unsupported_controllers", ())),
            unsupported_modules=tuple(data.get("unsupported_modules", ())),
            warnings=tuple(data.get("warnings", ())),
            schema_version=data.get("schema_version", "0.1"),
        )
