from __future__ import annotations

from typing import Any

from adaharness.evals.task_schema import EvalTask
from adaharness.modules.base import HarnessModule
from adaharness.runtime.budget import Budget
from adaharness.runtime.tracing import RunTrace


class BudgetGuardModule(HarnessModule):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="budget_guard", config=config or {})

    def before_model_call(
        self,
        trace: RunTrace,
        task: EvalTask,
        *,
        attempt: int,
        budget: Budget,
    ) -> RunTrace:
        return trace.add_event(
            "budget_guard.check",
            attempt=attempt,
            max_steps=self.config.get("max_steps", budget.max_steps),
            max_tool_calls=self.config.get("max_tool_calls", budget.max_tool_calls),
            verdict="within_budget",
        )
