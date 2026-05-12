from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from adaharness.runtime.tracing import RunTrace


@dataclass(frozen=True)
class HarnessModule:
    """Small runtime unit assembled from a ModuleSpec."""

    name: str
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "config", dict(self.config))

    def on_start(self, trace: RunTrace) -> RunTrace:
        return trace.add_event("module_enabled", module=self.name, config=self.config)
