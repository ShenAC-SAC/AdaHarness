from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from adaharness.policies.schema import HarnessPolicy


@dataclass(frozen=True)
class TraceEvent:
    event_type: str
    payload: dict[str, Any]
    timestamp: str

    @classmethod
    def create(cls, event_type: str, payload: dict[str, Any]) -> "TraceEvent":
        return cls(
            event_type=event_type,
            payload=payload,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunTrace:
    run_id: str
    task_id: str
    model_name: str
    harness_name: str
    policy: HarnessPolicy
    events: tuple[TraceEvent, ...]
    started_at: str
    ended_at: str | None = None

    @classmethod
    def start(
        cls,
        *,
        task_id: str,
        model_name: str,
        harness_name: str,
        policy: HarnessPolicy,
    ) -> "RunTrace":
        return cls(
            run_id=f"run_{uuid4().hex[:12]}",
            task_id=task_id,
            model_name=model_name,
            harness_name=harness_name,
            policy=policy,
            events=(),
            started_at=datetime.now(timezone.utc).isoformat(),
        )

    def add_event(self, event_type: str, **payload: Any) -> "RunTrace":
        return RunTrace(
            run_id=self.run_id,
            task_id=self.task_id,
            model_name=self.model_name,
            harness_name=self.harness_name,
            policy=self.policy,
            events=(*self.events, TraceEvent.create(event_type, payload)),
            started_at=self.started_at,
            ended_at=self.ended_at,
        )

    def finish(self) -> "RunTrace":
        return RunTrace(
            run_id=self.run_id,
            task_id=self.task_id,
            model_name=self.model_name,
            harness_name=self.harness_name,
            policy=self.policy,
            events=self.events,
            started_at=self.started_at,
            ended_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "task_id": self.task_id,
            "model_name": self.model_name,
            "harness_name": self.harness_name,
            "policy": self.policy.to_dict(),
            "events": [event.to_dict() for event in self.events],
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }
