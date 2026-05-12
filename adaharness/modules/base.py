from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from adaharness.evals.task_schema import EvalTask
from adaharness.models.base import ModelResponse
from adaharness.runtime.budget import Budget
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

    def before_model_call(
        self,
        trace: RunTrace,
        task: EvalTask,
        *,
        attempt: int,
        budget: Budget,
    ) -> RunTrace:
        return trace

    def after_model_call(
        self,
        trace: RunTrace,
        task: EvalTask,
        response: ModelResponse,
        *,
        attempt: int,
    ) -> RunTrace:
        return trace

    def verification_failed(self, response: ModelResponse) -> bool:
        return False

    def should_retry(
        self,
        *,
        verification_failed: bool,
        attempt: int,
    ) -> bool:
        return False

    def on_retry(self, trace: RunTrace, *, attempt: int, reason: str) -> RunTrace:
        return trace
