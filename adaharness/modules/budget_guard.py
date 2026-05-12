from __future__ import annotations

from typing import Any

from adaharness.modules.base import HarnessModule


class BudgetGuardModule(HarnessModule):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="budget_guard", config=config or {})
