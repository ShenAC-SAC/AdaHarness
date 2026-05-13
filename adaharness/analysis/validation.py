from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass

from adaharness.analysis.traces import TraceEvent


CANONICAL_EVENTS = (
    "model_call",
    "planner",
    "verifier",
    "retry",
    "tool_call",
    "tool_result_ignored",
    "subagent",
    "context",
    "final",
)

EVENT_ALIASES = {
    "plan": "planner",
    "verification": "verifier",
    "tool": "tool_call",
}


@dataclass(frozen=True)
class TraceValidationWarning:
    code: str
    severity: str
    message: str
    evidence: tuple[str, ...]
    task_id: str | None = None
    event: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", tuple(self.evidence))

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def validate_trace_events(events: tuple[TraceEvent, ...]) -> tuple[TraceValidationWarning, ...]:
    warnings: list[TraceValidationWarning] = []
    warnings.extend(_unknown_event_warnings(events))
    warnings.extend(_final_event_warnings(events))
    warnings.extend(_missing_evidence_warnings(events))
    return tuple(warnings)


def canonical_event_name(event_name: str) -> str | None:
    normalized = event_name.lower()
    suffix = normalized.rsplit(".", 1)[-1]
    if normalized in CANONICAL_EVENTS:
        return normalized
    if suffix in CANONICAL_EVENTS:
        return suffix
    return EVENT_ALIASES.get(normalized) or EVENT_ALIASES.get(suffix)


def _unknown_event_warnings(events: tuple[TraceEvent, ...]) -> list[TraceValidationWarning]:
    counts = Counter(event.event for event in events if canonical_event_name(event.event) is None)
    return [
        TraceValidationWarning(
            code="unknown_event",
            severity="low",
            message=f"Unknown trace event {event_name!r}; metrics may ignore it.",
            event=event_name,
            evidence=(f"count={count}",),
        )
        for event_name, count in sorted(counts.items())
    ]


def _final_event_warnings(events: tuple[TraceEvent, ...]) -> list[TraceValidationWarning]:
    by_task: dict[str, list[TraceEvent]] = defaultdict(list)
    for event in events:
        by_task[event.task_id].append(event)

    missing_final = []
    multiple_final = []
    for task_id, task_events in by_task.items():
        final_count = sum(1 for event in task_events if event.is_event("final"))
        if final_count == 0:
            missing_final.append(task_id)
        elif final_count > 1:
            multiple_final.append(task_id)

    warnings = []
    if missing_final:
        warnings.append(
            TraceValidationWarning(
                code="missing_final",
                severity="medium",
                message="Some tasks have no final event; success and failure rates may be incomplete.",
                evidence=_task_sample_evidence(missing_final),
            )
        )
    if multiple_final:
        warnings.append(
            TraceValidationWarning(
                code="multiple_final",
                severity="medium",
                message="Some tasks have multiple final events; success and failure rates may be ambiguous.",
                evidence=_task_sample_evidence(multiple_final),
            )
        )
    return warnings


def _missing_evidence_warnings(events: tuple[TraceEvent, ...]) -> list[TraceValidationWarning]:
    warnings = []
    if not any(event.cost is not None for event in events):
        warnings.append(
            TraceValidationWarning(
                code="missing_cost",
                severity="low",
                message="No cost values were recorded; cost-share diagnostics have weak evidence.",
                evidence=("cost_fields=0",),
            )
        )
    if not any(event.latency_ms is not None for event in events):
        warnings.append(
            TraceValidationWarning(
                code="missing_latency",
                severity="low",
                message="No latency values were recorded; latency diagnostics have weak evidence.",
                evidence=("latency_ms_fields=0",),
            )
        )
    return warnings


def _task_sample_evidence(task_ids: list[str]) -> tuple[str, ...]:
    sample = ", ".join(sorted(task_ids)[:5])
    return (f"task_count={len(task_ids)}", f"sample={sample}")
