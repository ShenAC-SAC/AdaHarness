from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from time import perf_counter
from types import TracebackType
from typing import Any


TRACE_SCHEMA_VERSION = "0.1"


class TraceRecorder:
    """Append AdaHarness-compatible JSONL trace events.

    The recorder only writes events. It does not install hooks, call tools,
    mutate prompts, manage retries, or control the host runtime.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        model: str | None = None,
        policy: str | None = None,
        schema_version: str = TRACE_SCHEMA_VERSION,
    ) -> None:
        self.path = Path(path)
        self.model = model
        self.policy = policy
        self.schema_version = schema_version

    def task(
        self,
        task_id: str,
        *,
        model: str | None = None,
        policy: str | None = None,
    ) -> "TaskTrace":
        return TaskTrace(
            recorder=self,
            task_id=task_id,
            model=model,
            policy=policy,
        )

    def emit(
        self,
        *,
        task_id: str,
        event: str,
        status: str | None = None,
        model: str | None = None,
        policy: str | None = None,
        control: str | None = None,
        reason: str | None = None,
        success: bool | None = None,
        cost: float | None = None,
        latency_ms: float | None = None,
        tokens: int | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "task_id": str(task_id),
            "event": event,
        }
        _set_if_present(data, "status", status)
        _set_if_present(data, "model", model if model is not None else self.model)
        _set_if_present(data, "policy", policy if policy is not None else self.policy)
        _set_if_present(data, "control", control)
        _set_if_present(data, "reason", reason)
        _set_if_present(data, "success", success)
        _set_if_present(data, "cost", cost)
        _set_if_present(data, "latency_ms", latency_ms)
        _set_if_present(data, "tokens", tokens)
        for key, value in extra.items():
            _set_if_present(data, key, value)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
        return data


@dataclass(frozen=True)
class TaskTrace:
    recorder: TraceRecorder
    task_id: str
    model: str | None = None
    policy: str | None = None

    def emit(self, event: str, **fields: Any) -> dict[str, Any]:
        return self.recorder.emit(
            task_id=self.task_id,
            event=event,
            model=self.model,
            policy=self.policy,
            **fields,
        )

    def model_call(self, **fields: Any) -> dict[str, Any]:
        return self.emit("model_call", **fields)

    def planner(self, **fields: Any) -> dict[str, Any]:
        return self.emit("planner", **fields)

    def verifier(self, **fields: Any) -> dict[str, Any]:
        return self.emit("verifier", **fields)

    def retry(self, *, reason: str, **fields: Any) -> dict[str, Any]:
        return self.emit("retry", reason=reason, **fields)

    def tool_call(self, *, tool: str | None = None, **fields: Any) -> dict[str, Any]:
        return self.emit("tool_call", tool=tool, **fields)

    def tool_result_ignored(self, **fields: Any) -> dict[str, Any]:
        return self.emit("tool_result_ignored", reason="tool_result_ignored", **fields)

    def subagent(self, **fields: Any) -> dict[str, Any]:
        return self.emit("subagent", **fields)

    def context(self, **fields: Any) -> dict[str, Any]:
        return self.emit("context", **fields)

    def final(self, *, success: bool, **fields: Any) -> dict[str, Any]:
        return self.emit("final", success=success, **fields)

    def timed(self, event: str, **fields: Any) -> "TraceSpan":
        return TraceSpan(trace=self, event=event, fields=fields)


@dataclass
class TraceSpan:
    trace: TaskTrace
    event: str
    fields: dict[str, Any]
    _started_at: float | None = None

    def __enter__(self) -> "TraceSpan":
        self._started_at = perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        started_at = self._started_at if self._started_at is not None else perf_counter()
        fields = dict(self.fields)
        fields.setdefault("latency_ms", (perf_counter() - started_at) * 1000)
        if exc_type is None:
            fields.setdefault("status", "success")
        else:
            fields.setdefault("status", "failed")
            fields.setdefault("reason", exc_type.__name__)
        self.trace.emit(self.event, **fields)
        return False


def _set_if_present(data: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        data[key] = value
