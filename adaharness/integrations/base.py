from __future__ import annotations

from typing import Any, Protocol

from adaharness.runtime.tracing import RunTrace


class ExternalTraceAdapter(Protocol):
    name: str

    def can_parse(self, source: dict[str, Any]) -> bool:
        ...

    def parse(self, source: dict[str, Any]) -> RunTrace:
        ...
