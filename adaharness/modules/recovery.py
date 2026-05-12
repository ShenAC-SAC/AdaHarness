from __future__ import annotations

from typing import Any

from adaharness.modules.base import HarnessModule
from adaharness.runtime.tracing import RunTrace


class RecoveryModule(HarnessModule):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="recovery", config=config or {})

    def on_retry(self, trace: RunTrace, *, attempt: int, reason: str) -> RunTrace:
        return trace.add_event(
            "recovery.recover",
            recover_from=self.config.get("recover_from", []),
            attempt=attempt,
            reason=reason,
        )
