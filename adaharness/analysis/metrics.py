from __future__ import annotations

from dataclasses import asdict, dataclass

from adaharness.analysis.traces import TraceEvent


@dataclass(frozen=True)
class TraceMetrics:
    task_count: int
    final_count: int
    success_rate: float
    failure_rate: float
    total_cost: float
    total_latency_ms: float
    verifier_events: int
    verifier_failures: int
    verifier_catch_rate: float
    verifier_cost_share: float
    planner_events: int
    planner_task_rate: float
    planner_latency_share: float
    retry_events: int
    retry_task_rate: float
    retry_success_rate: float
    retry_waste_rate: float
    failed_without_retry_rate: float
    tool_call_count: int
    tool_failure_rate: float
    tool_result_ignored_rate: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def compute_trace_metrics(events: tuple[TraceEvent, ...]) -> TraceMetrics:
    if not events:
        raise ValueError("events must not be empty")

    task_ids = {event.task_id for event in events}
    final_events = [event for event in events if event.is_event("final")]
    successful_tasks = {
        event.task_id
        for event in final_events
        if event.success is True or event.status in {"pass", "passed", "success"}
    }
    failed_tasks = {
        event.task_id
        for event in final_events
        if event.success is False or event.status in {"fail", "failed", "error"}
    }
    total_cost = sum(event.cost or 0.0 for event in events)
    total_latency = sum(event.latency_ms or 0.0 for event in events)

    verifier_events = [event for event in events if event.is_event("verifier", "verification")]
    verifier_failures = [
        event
        for event in verifier_events
        if event.status in {"fail", "failed", "error"} or event.success is False
    ]
    verifier_cost = sum(event.cost or 0.0 for event in verifier_events)

    planner_events = [event for event in events if event.is_event("planner", "plan")]
    planner_latency = sum(event.latency_ms or 0.0 for event in planner_events)
    planner_tasks = {event.task_id for event in planner_events}

    retry_events = [event for event in events if event.is_event("retry")]
    retry_tasks = {event.task_id for event in retry_events}
    retried_successes = retry_tasks & successful_tasks
    retried_failures = retry_tasks & failed_tasks
    failed_without_retry = failed_tasks - retry_tasks

    tool_events = [event for event in events if event.is_event("tool_call", "tool")]
    tool_failures = [
        event
        for event in tool_events
        if event.status in {"fail", "failed", "error"} or event.success is False
    ]
    ignored_tool_events = [
        event
        for event in events
        if event.is_event("tool_result_ignored") or event.reason == "tool_result_ignored"
    ]

    task_count = len(task_ids)
    final_count = len(final_events)
    success_rate = _ratio(len(successful_tasks), final_count)
    failure_rate = _ratio(len(failed_tasks), final_count)
    return TraceMetrics(
        task_count=task_count,
        final_count=final_count,
        success_rate=success_rate,
        failure_rate=failure_rate,
        total_cost=total_cost,
        total_latency_ms=total_latency,
        verifier_events=len(verifier_events),
        verifier_failures=len(verifier_failures),
        verifier_catch_rate=_ratio(len(verifier_failures), len(verifier_events)),
        verifier_cost_share=_ratio(verifier_cost, total_cost),
        planner_events=len(planner_events),
        planner_task_rate=_ratio(len(planner_tasks), task_count),
        planner_latency_share=_ratio(planner_latency, total_latency),
        retry_events=len(retry_events),
        retry_task_rate=_ratio(len(retry_tasks), task_count),
        retry_success_rate=_ratio(len(retried_successes), len(retry_tasks)),
        retry_waste_rate=_ratio(len(retried_failures), len(retry_tasks)),
        failed_without_retry_rate=_ratio(len(failed_without_retry), max(1, len(failed_tasks))),
        tool_call_count=len(tool_events),
        tool_failure_rate=_ratio(len(tool_failures), len(tool_events)),
        tool_result_ignored_rate=_ratio(len(ignored_tool_events), max(1, len(tool_events))),
    )


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator
