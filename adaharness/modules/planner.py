from __future__ import annotations

from typing import Any

from adaharness.evals.task_schema import EvalTask
from adaharness.modules.base import HarnessModule
from adaharness.runtime.budget import Budget
from adaharness.runtime.tracing import RunTrace


class PlannerModule(HarnessModule):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="planner", config=config or {})

    def before_model_call(
        self,
        trace: RunTrace,
        task: EvalTask,
        *,
        attempt: int,
        budget: Budget,
    ) -> RunTrace:
        if attempt > 1:
            return trace
        return trace.add_event(
            "planner.plan",
            depth=self.config.get("depth"),
            max_plan_steps=self.config.get("max_plan_steps"),
            task_id=task.id,
        )
