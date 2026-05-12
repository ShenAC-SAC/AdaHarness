from __future__ import annotations

from typing import Any

from adaharness.evals.task_schema import EvalTask
from adaharness.models.base import ModelResponse
from adaharness.modules.base import HarnessModule
from adaharness.runtime.tracing import RunTrace


class VerifierModule(HarnessModule):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="verifier", config=config or {})

    def after_model_call(
        self,
        trace: RunTrace,
        task: EvalTask,
        response: ModelResponse,
        *,
        attempt: int,
    ) -> RunTrace:
        verdict = "failed" if self.verification_failed(response) else "passed"
        return trace.add_event(
            "verifier.check",
            strength=self.config.get("strength"),
            checkpoints=self.config.get("checkpoints", []),
            verdict=verdict,
            attempt=attempt,
            task_id=task.id,
        )

    def verification_failed(self, response: ModelResponse) -> bool:
        return not response.text.strip()
