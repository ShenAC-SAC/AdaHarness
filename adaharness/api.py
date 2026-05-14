from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from adaharness.analysis import (
    assess_harness_fit,
    compute_trace_metrics,
    diagnose_harness,
    load_diagnostic_config,
    load_trace_events,
    recommend_policy_changes,
    render_analysis_report,
    validate_trace_events,
)


def analyze_traces(
    traces: list[str | Path],
    *,
    current_policy: dict[str, Any] | str | Path | None = None,
    diagnostics_config: str | Path | None = None,
) -> dict[str, Any]:
    """Analyze exported agent traces and return report-ready artifacts."""

    events = load_trace_events([Path(path) for path in traces])
    config = load_diagnostic_config(diagnostics_config)
    trace_warnings = validate_trace_events(events)
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
    report = render_analysis_report(
        metrics=metrics,
        fit_verdict=fit_verdict,
        signals=signals,
        changes=changes,
        trace_warnings=trace_warnings,
    )
    return {
        "diagnostics_config": config.to_dict(),
        "metrics": metrics.to_dict(),
        "fit_verdict": fit_verdict.to_dict(),
        "trace_warnings": [warning.to_dict() for warning in trace_warnings],
        "diagnosis": {"signals": [signal.to_dict() for signal in signals]},
        "policy_diff": {"changes": [change.to_dict() for change in changes]},
        "report": report,
    }


def _policy_dict(value: dict[str, Any] | str | Path | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get("policy", value)
    data = json.loads(Path(value).read_text(encoding="utf-8"))
    return data.get("policy", data)
