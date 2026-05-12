from __future__ import annotations

from typing import Any

from adaharness.modules.base import HarnessModule


class RecoveryModule(HarnessModule):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="recovery", config=config or {})
