from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from adaharness.policies.presets import BARE_POLICY
from adaharness.policies.schema import HarnessPolicy
from adaharness.runtime.tracing import RunTrace, TraceEvent


class GenericJSONTraceAdapter:
    name = "generic_json"

    def can_parse(self, source: dict[str, Any]) -> bool:
        return "events" in source and isinstance(source["events"], list)

    def parse(self, source: dict[str, Any]) -> RunTrace:
        policy = HarnessPolicy.from_dict(source["policy"]) if "policy" in source else BARE_POLICY
        return RunTrace(
            run_id=source.get("run_id", f"external_{uuid4().hex[:12]}"),
            task_id=source.get("task_id", "external_task"),
            model_name=source.get("model_name", "external_model"),
            harness_name=source.get("harness_name", "external_harness"),
            policy=policy,
            events=tuple(_event_from_external(event) for event in source.get("events", [])),
            started_at=source.get("started_at", _now()),
            ended_at=source.get("ended_at"),
        )


def _event_from_external(data: dict[str, Any]) -> TraceEvent:
    if "event_type" in data and "payload" in data and "timestamp" in data:
        return TraceEvent.from_dict(data)
    event_type = data.get("event_type", data.get("type", "external_event"))
    payload = data.get("payload", {key: value for key, value in data.items() if key not in {"type", "event_type"}})
    return TraceEvent(
        event_type=event_type,
        payload=payload,
        timestamp=data.get("timestamp", _now()),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
