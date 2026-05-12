from __future__ import annotations

from typing import Any

from adaharness.evals.task_schema import EvalTask
from adaharness.modules.base import HarnessModule
from adaharness.runtime.budget import Budget
from adaharness.runtime.tracing import RunTrace


class ToolGatekeeperModule(HarnessModule):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="tool_gatekeeper", config=config or {})

    def before_model_call(
        self,
        trace: RunTrace,
        task: EvalTask,
        *,
        attempt: int,
        budget: Budget,
    ) -> RunTrace:
        return trace.add_event(
            "tool_gatekeeper.check",
            strictness=self.config.get("strictness"),
            task_category=task.category,
            verdict="allowed",
            attempt=attempt,
        )
