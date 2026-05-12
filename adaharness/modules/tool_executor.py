from __future__ import annotations

from typing import Any

from adaharness.evals.task_schema import EvalTask
from adaharness.modules.base import HarnessModule
from adaharness.runtime.budget import Budget
from adaharness.runtime.tracing import RunTrace


class ToolExecutorModule(HarnessModule):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="tool_executor", config=config or {})

    def before_model_call(
        self,
        trace: RunTrace,
        task: EvalTask,
        *,
        attempt: int,
        budget: Budget,
    ) -> RunTrace:
        if task.category != "tool_use":
            return trace
        return trace.add_event(
            "tool_executor.ready",
            mode=self.config.get("mode"),
            task_id=task.id,
            attempt=attempt,
        )
