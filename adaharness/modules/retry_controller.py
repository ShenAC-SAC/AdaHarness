from __future__ import annotations

from typing import Any

from adaharness.modules.base import HarnessModule
from adaharness.runtime.tracing import RunTrace


class RetryControllerModule(HarnessModule):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="retry_controller", config=config or {})

    def should_retry(
        self,
        *,
        verification_failed: bool,
        attempt: int,
    ) -> bool:
        return verification_failed and attempt <= int(self.config.get("max_retries", 0))

    def on_retry(self, trace: RunTrace, *, attempt: int, reason: str) -> RunTrace:
        return trace.add_event(
            "retry_controller.retry",
            policy=self.config.get("policy"),
            attempt=attempt,
            reason=reason,
        )
