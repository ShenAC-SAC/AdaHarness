from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class TraceEvent:
    """Small JSONL event exported by a host agent project."""

    task_id: str
    event: str
    status: str | None = None
    model: str | None = None
    policy: str | None = None
    task_type: str | None = None
    control: str | None = None
    reason: str | None = None
    success: bool | None = None
    cost: float | None = None
    latency_ms: float | None = None
    tokens: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "raw", dict(self.raw))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceEvent":
        if "task_id" not in data:
            raise ValueError("trace event requires task_id")
        event = data.get("event", data.get("event_type"))
        if not event:
            raise ValueError("trace event requires event")
        return cls(
            task_id=str(data["task_id"]),
            event=str(event),
            status=_optional_str(data.get("status")),
            model=_optional_str(data.get("model", data.get("model_name"))),
            policy=_optional_str(data.get("policy")),
            task_type=_optional_str(data.get("task_type")),
            control=_optional_str(data.get("control")),
            reason=_optional_str(data.get("reason")),
            success=_optional_bool(data.get("success")),
            cost=_optional_float(data.get("cost", data.get("estimated_cost"))),
            latency_ms=_optional_float(data.get("latency_ms", data.get("estimated_latency_ms"))),
            tokens=_optional_int(data.get("tokens", data.get("total_tokens"))),
            raw=data,
        )

    def to_dict(self) -> dict[str, Any]:
        data = dict(self.raw)
        data.update(
            {
                "task_id": self.task_id,
                "event": self.event,
            }
        )
        for key in (
            "status",
            "model",
            "policy",
            "task_type",
            "control",
            "reason",
            "success",
            "cost",
            "latency_ms",
            "tokens",
        ):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        return data

    def is_event(self, *names: str) -> bool:
        normalized = self.event.lower()
        return any(normalized == name or normalized.endswith(f".{name}") for name in names)


def load_trace_events(paths: list[Path]) -> tuple[TraceEvent, ...]:
    events: list[TraceEvent] = []
    for path in paths:
        events.extend(_load_trace_file(path))
    return tuple(events)


def _load_trace_file(path: Path) -> list[TraceEvent]:
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [TraceEvent.from_dict(item) for item in data]
        if "events" in data:
            return [TraceEvent.from_dict(item) for item in data["events"]]
        return [TraceEvent.from_dict(data)]

    events = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            events.append(TraceEvent.from_dict(json.loads(stripped)))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{line_number}") from exc
    return events


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "pass", "passed", "success"}
    return bool(value)


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)
