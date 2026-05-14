from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from adaharness.analysis import (
    AnalysisResult,
    DiagnosticConfig,
    TraceEvent,
    TraceValidationWarning,
    assess_harness_fit,
    compute_trace_metrics,
    diagnose_harness,
    group_trace_events,
    load_diagnostic_config,
    load_trace_events,
    mixed_group_warnings,
    normalize_group_by,
    recommend_policy_changes,
    render_analysis_report,
    validate_trace_events,
)


def analyze_traces(
    traces: list[str | Path],
    *,
    current_policy: dict[str, Any] | str | Path | None = None,
    diagnostics_config: str | Path | None = None,
    group_by: str | list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Analyze exported agent traces and return report-ready artifacts."""

    events = load_trace_events([Path(path) for path in traces])
    config = load_diagnostic_config(diagnostics_config)
    group_fields = normalize_group_by(group_by)
    trace_warnings = validate_trace_events(events) + mixed_group_warnings(
        events,
        grouped_fields=group_fields,
    )
    result = _analyze_event_set(
        events=events,
        config=config,
        current_policy=current_policy,
        trace_warnings=trace_warnings,
    )
    grouped_results = tuple(
        _analyze_event_set(
            events=group.events,
            config=config,
            current_policy=current_policy,
            trace_warnings=validate_trace_events(group.events)
            + mixed_group_warnings(group.events, grouped_fields=group_fields),
            group=group.values,
        )
        for group in group_trace_events(events, group_fields)
    )
    report = render_analysis_report(result=result, grouped_results=grouped_results)
    data = {
        "diagnostics_config": config.to_dict(),
        "group_by": list(group_fields),
        **result.to_dict(),
        "groups": [grouped_result.to_dict() for grouped_result in grouped_results],
        "report": report,
    }
    return data


def _analyze_event_set(
    *,
    events: tuple[TraceEvent, ...],
    config: DiagnosticConfig,
    current_policy: dict[str, Any] | str | Path | None = None,
    trace_warnings: tuple[TraceValidationWarning, ...] = (),
    group: dict[str, str] | None = None,
) -> AnalysisResult:
    metrics = compute_trace_metrics(events)
    signals = diagnose_harness(metrics, config=config)
    fit_verdict = assess_harness_fit(
        metrics=metrics,
        signals=signals,
        trace_warnings=trace_warnings,
    )
    changes = recommend_policy_changes(
        signals,
        current_policy=_policy_dict(current_policy),
    )
    return AnalysisResult(
        metrics=metrics,
        fit_verdict=fit_verdict,
        trace_warnings=trace_warnings,
        signals=signals,
        changes=changes,
        group=group or {},
    )


def _policy_dict(value: dict[str, Any] | str | Path | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get("policy", value)
    data = json.loads(Path(value).read_text(encoding="utf-8"))
    return data.get("policy", data)
