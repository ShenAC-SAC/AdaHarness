from __future__ import annotations

from dataclasses import dataclass, field

from adaharness.runtime.tracing import TraceEvent


@dataclass
class RuntimeState:
    step_count: int = 0
    tool_call_count: int = 0
    retry_count: int = 0
    trace: list[TraceEvent] = field(default_factory=list)

    def record(self, event_type: str, **payload: object) -> None:
        self.trace.append(TraceEvent.create(event_type, payload))
