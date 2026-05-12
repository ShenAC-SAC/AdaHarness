from __future__ import annotations

from typing import Any

from adaharness.modules.base import HarnessModule


class TraceModule(HarnessModule):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="trace", config=config or {})
