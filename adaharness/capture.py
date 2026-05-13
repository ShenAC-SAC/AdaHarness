from __future__ import annotations

from dataclasses import asdict, dataclass, field
from importlib.resources import files
import json
from pathlib import Path
import re
import subprocess
from time import perf_counter
from typing import Any

from adaharness.trace import TaskTrace, TraceRecorder


EVENT_PREFIX = "ADAHARNESS_EVENT "
BUILTIN_TASK_SUITES = {
    "connectivity-smoke": "tasks/connectivity-smoke.jsonl",
    "ifeval-lite": "tasks/ifeval-lite.jsonl",
}
DEFAULT_TASK_SUITE = "ifeval-lite"


@dataclass(frozen=True)
class CaptureTask:
    task_id: str
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaptureTask":
        task_id = data.get("task_id", data.get("id", data.get("name")))
        if not task_id:
            raise ValueError("capture task requires task_id, id, or name")
        return cls(task_id=str(task_id), data=dict(data))

    @property
    def expected_contains(self) -> str | None:
        value = self.data.get("expected_contains")
        return None if value is None else str(value)

    @property
    def expected_regex(self) -> str | None:
        value = self.data.get("expected_regex")
        return None if value is None else str(value)

    @property
    def judges(self) -> tuple[dict[str, Any], ...]:
        judge = self.data.get("judge")
        if isinstance(judge, list):
            return tuple(dict(item) for item in judge)
        if isinstance(judge, dict):
            return (dict(judge),)

        judges = []
        if self.expected_contains is not None:
            judges.append({"type": "contains", "value": self.expected_contains})
        if self.expected_regex is not None:
            judges.append({"type": "regex", "pattern": self.expected_regex})
        return tuple(judges)

    def format_command(self, command: list[str]) -> list[str]:
        return [_format_template(part, self.data) for part in command]

    def stdin_value(self, field_name: str | None) -> str | None:
        if not field_name:
            return None
        if field_name not in self.data:
            raise ValueError(f"task {self.task_id!r} has no stdin field {field_name!r}")
        return str(self.data[field_name])


@dataclass(frozen=True)
class CaptureTaskResult:
    task_id: str
    success: bool
    status: str
    exit_code: int | None
    latency_ms: float
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CaptureSummary:
    trace_path: str
    task_count: int
    success_count: int
    failure_count: int
    results: tuple[CaptureTaskResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_path": self.trace_path,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "results": [result.to_dict() for result in self.results],
        }


def load_capture_tasks(path: Path) -> tuple[CaptureTask, ...]:
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return tuple(CaptureTask.from_dict(item) for item in data)
        if "tasks" in data:
            return tuple(CaptureTask.from_dict(item) for item in data["tasks"])
        return (CaptureTask.from_dict(data),)

    tasks = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            tasks.append(CaptureTask.from_dict(json.loads(stripped)))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{line_number}") from exc
    return tuple(tasks)


def load_builtin_capture_tasks(name: str) -> tuple[CaptureTask, ...]:
    if name not in BUILTIN_TASK_SUITES:
        supported = ", ".join(sorted(BUILTIN_TASK_SUITES))
        raise ValueError(f"unknown capture suite {name!r}. Expected one of: {supported}")
    resource = files("adaharness.templates").joinpath(BUILTIN_TASK_SUITES[name])
    tasks = []
    for line_number, line in enumerate(resource.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            tasks.append(CaptureTask.from_dict(json.loads(stripped)))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in built-in suite {name}:{line_number}") from exc
    return tuple(tasks)


def capture_command_runs(
    *,
    tasks: tuple[CaptureTask, ...],
    command: list[str],
    out_path: Path,
    model: str | None = None,
    policy: str | None = None,
    timeout: float | None = None,
    stdin_field: str | None = None,
    append: bool = False,
    include_output: bool = False,
    event_prefix: str = EVENT_PREFIX,
) -> CaptureSummary:
    if not tasks:
        raise ValueError("capture requires at least one task")
    if not command:
        raise ValueError("capture requires a command after --")
    if out_path.exists() and not append:
        out_path.unlink()

    recorder = TraceRecorder(out_path, model=model, policy=policy)
    results = []
    for task in tasks:
        result = _run_one_task(
            task=task,
            command=command,
            recorder=recorder,
            timeout=timeout,
            stdin_field=stdin_field,
            include_output=include_output,
            event_prefix=event_prefix,
        )
        results.append(result)

    success_count = sum(1 for result in results if result.success)
    return CaptureSummary(
        trace_path=str(out_path),
        task_count=len(results),
        success_count=success_count,
        failure_count=len(results) - success_count,
        results=tuple(results),
    )


def _run_one_task(
    *,
    task: CaptureTask,
    command: list[str],
    recorder: TraceRecorder,
    timeout: float | None,
    stdin_field: str | None,
    include_output: bool,
    event_prefix: str,
) -> CaptureTaskResult:
    trace = recorder.task(task.task_id)
    started_at = perf_counter()
    formatted_command = task.format_command(command)
    stdin = task.stdin_value(stdin_field)
    try:
        completed = subprocess.run(
            formatted_command,
            input=stdin,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        latency_ms = (perf_counter() - started_at) * 1000
        answer_output = _answer_output(completed.stdout, event_prefix)
        success, reason = _judge_success(task, completed.returncode, answer_output)
        status = "success" if completed.returncode == 0 else "failed"
        model_fields = _output_fields(
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            include_output=include_output,
        )
        trace.model_call(status=status, latency_ms=latency_ms, reason=reason, **model_fields)
        marker_errors = _emit_embedded_events(
            trace=trace,
            output=f"{completed.stdout}\n{completed.stderr}",
            event_prefix=event_prefix,
        )
        if marker_errors:
            trace.context(status="failed", reason="invalid_embedded_event", errors=marker_errors)
        trace.final(
            success=success,
            status="success" if success else "failed",
            latency_ms=latency_ms,
            reason=reason,
            exit_code=completed.returncode,
        )
        return CaptureTaskResult(
            task_id=task.task_id,
            success=success,
            status="success" if success else "failed",
            exit_code=completed.returncode,
            latency_ms=latency_ms,
            reason=reason,
        )
    except subprocess.TimeoutExpired as exc:
        latency_ms = (perf_counter() - started_at) * 1000
        stdout = _timeout_output(exc.stdout)
        stderr = _timeout_output(exc.stderr)
        fields = _output_fields(
            stdout=stdout,
            stderr=stderr,
            exit_code=None,
            include_output=include_output,
        )
        trace.model_call(status="failed", latency_ms=latency_ms, reason="timeout", **fields)
        marker_errors = _emit_embedded_events(
            trace=trace,
            output=f"{stdout}\n{stderr}",
            event_prefix=event_prefix,
        )
        if marker_errors:
            trace.context(status="failed", reason="invalid_embedded_event", errors=marker_errors)
        trace.final(success=False, status="failed", latency_ms=latency_ms, reason="timeout")
        return CaptureTaskResult(
            task_id=task.task_id,
            success=False,
            status="failed",
            exit_code=None,
            latency_ms=latency_ms,
            reason="timeout",
        )


def _judge_success(task: CaptureTask, exit_code: int, stdout: str) -> tuple[bool, str | None]:
    if exit_code != 0:
        return False, f"exit_code_{exit_code}"
    for judge in task.judges:
        passed, reason = _judge_output(judge, stdout)
        if not passed:
            return False, reason
    return True, None


def _judge_output(judge: dict[str, Any], stdout: str) -> tuple[bool, str | None]:
    judge_type = str(judge.get("type", "")).lower()
    if judge_type == "contains":
        value = str(judge.get("value", ""))
        return (True, None) if value in stdout else (False, "contains_missing")
    if judge_type == "not_contains":
        value = str(judge.get("value", ""))
        return (True, None) if value not in stdout else (False, "forbidden_text_present")
    if judge_type == "regex":
        pattern = str(judge.get("pattern", ""))
        return (True, None) if re.search(pattern, stdout) else (False, "regex_missing")
    if judge_type == "exact":
        value = str(judge.get("value", ""))
        return (True, None) if stdout.strip() == value else (False, "exact_mismatch")
    if judge_type == "json_field":
        return _judge_json_field(judge, stdout)
    raise ValueError(f"unsupported judge type {judge_type!r}")


def _judge_json_field(judge: dict[str, Any], stdout: str) -> tuple[bool, str | None]:
    try:
        data = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return False, "invalid_json"
    field = str(judge.get("field", ""))
    if not field:
        raise ValueError("json_field judge requires field")
    if field not in data:
        return False, "json_field_missing"
    expected = judge.get("value")
    if "value" in judge and data[field] != expected:
        return False, "json_field_mismatch"
    return True, None


def _emit_embedded_events(*, trace: TaskTrace, output: str, event_prefix: str) -> list[str]:
    errors = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped.startswith(event_prefix):
            continue
        payload = stripped[len(event_prefix):].strip()
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            errors.append("invalid_json")
            continue
        event = data.pop("event", None)
        if not event:
            errors.append("missing_event")
            continue
        data.pop("task_id", None)
        trace.emit(str(event), **data)
    return errors


def _output_fields(
    *,
    stdout: str,
    stderr: str,
    exit_code: int | None,
    include_output: bool,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "stdout_chars": len(stdout),
        "stderr_chars": len(stderr),
    }
    if exit_code is not None:
        fields["exit_code"] = exit_code
    if include_output:
        fields["stdout"] = stdout
        fields["stderr"] = stderr
    return fields


def _timeout_output(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _answer_output(stdout: str, event_prefix: str) -> str:
    lines = [line for line in stdout.splitlines() if not line.strip().startswith(event_prefix)]
    return "\n".join(lines).strip()


def _format_template(template: str, data: dict[str, Any]) -> str:
    try:
        return template.format_map(_TaskFormatMap(data))
    except KeyError as exc:
        raise ValueError(f"task is missing command placeholder {exc.args[0]!r}") from exc


class _TaskFormatMap(dict[str, Any]):
    def __missing__(self, key: str) -> Any:
        raise KeyError(key)
