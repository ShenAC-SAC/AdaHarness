from __future__ import annotations

from adaharness.analysis.diagnostics import DiagnosticSignal
from adaharness.analysis.fit import FitVerdict
from adaharness.analysis.metrics import TraceMetrics
from adaharness.analysis.policy_diff import PolicyChange
from adaharness.analysis.result import AnalysisResult
from adaharness.analysis.validation import TraceValidationWarning


def render_analysis_report(
    *,
    result: AnalysisResult | None = None,
    grouped_results: tuple[AnalysisResult, ...] = (),
    metrics: TraceMetrics | None = None,
    fit_verdict: FitVerdict | None = None,
    signals: tuple[DiagnosticSignal, ...] | None = None,
    changes: tuple[PolicyChange, ...] | None = None,
    trace_warnings: tuple[TraceValidationWarning, ...] = (),
) -> str:
    if result is not None:
        metrics = result.metrics
        fit_verdict = result.fit_verdict
        signals = result.signals
        changes = result.changes
        trace_warnings = result.trace_warnings
    if metrics is None or fit_verdict is None or signals is None or changes is None:
        raise ValueError("render_analysis_report requires either result or metrics, fit_verdict, signals, and changes")

    lines = [
        "# AdaHarness Drift Report",
        "",
        "## Summary",
        "",
        f"- Fit verdict: {fit_verdict.status}",
        f"- Verdict confidence: {fit_verdict.confidence}",
        f"- Verdict summary: {fit_verdict.summary}",
        f"- Task count: {metrics.task_count}",
        f"- Success rate: {metrics.success_rate:.2f}",
        f"- Total cost: {metrics.total_cost:.4f}",
        f"- Total latency ms: {metrics.total_latency_ms:.0f}",
        "",
        "## Fit Verdict",
        "",
        f"- Status: `{fit_verdict.status}`",
        f"- Confidence: {fit_verdict.confidence}",
        f"- Summary: {fit_verdict.summary}",
        f"- Evidence count: {fit_verdict.evidence_count}",
        f"- Primary controls: {_format_controls(fit_verdict.primary_controls)}",
    ]
    for item in fit_verdict.evidence:
        lines.append(f"- Evidence: {item}")
    lines.extend(
        [
            "",
            "## Trace Quality",
            "",
        ]
    )
    if not trace_warnings:
        lines.append("- No trace quality warnings detected.")
    for warning in trace_warnings:
        lines.append(f"- **{warning.severity} / {warning.code}**: {warning.message}")
        for item in warning.evidence:
            lines.append(f"  - {item}")
    lines.extend(
        [
            "",
            "## Harness Metrics",
            "",
            f"- Verifier catch rate: {metrics.verifier_catch_rate:.2f}",
            f"- Verifier cost share: {metrics.verifier_cost_share:.2f}",
            f"- Planner latency share: {metrics.planner_latency_share:.2f}",
            f"- Retry success rate: {metrics.retry_success_rate:.2f}",
            f"- Retry waste rate: {metrics.retry_waste_rate:.2f}",
            f"- Tool failure rate: {metrics.tool_failure_rate:.2f}",
            f"- Tool result ignored rate: {metrics.tool_result_ignored_rate:.2f}",
            "",
            "## Diagnosis",
            "",
        ]
    )
    for signal in signals:
        lines.append(f"- **{signal.kind} / {signal.control} / {signal.severity}**: {signal.message}")
        lines.append(f"  - Confidence: {signal.confidence}")
        lines.append(f"  - Evidence count: {signal.evidence_count}")
        if signal.rule:
            lines.append(f"  - Rule: {signal.rule}")
        if signal.missing_data:
            lines.append(f"  - Missing data: {', '.join(signal.missing_data)}")
        for item in signal.evidence:
            lines.append(f"  - {item}")
    lines.extend(["", "## Suggested Policy Diff", ""])
    if not changes:
        lines.append("- No policy change suggested from current evidence.")
    for change in changes:
        lines.append(f"- `{change.field}`: `{change.from_value}` -> `{change.to_value}`")
        lines.append(f"  - Reason: {change.reason}")
        lines.append(f"  - Confidence: {change.confidence}")
        lines.append(f"  - Evidence count: {change.evidence_count}")
        for item in change.evidence:
            lines.append(f"  - Evidence: {item}")
    if grouped_results:
        lines.extend(["", "## Groups", ""])
        for grouped_result in grouped_results:
            lines.extend(_group_lines(grouped_result))
    return "\n".join(lines)


def _format_controls(controls: tuple[str, ...]) -> str:
    return ", ".join(f"`{control}`" for control in controls) if controls else "none"


def _group_lines(result: AnalysisResult) -> list[str]:
    lines = [
        f"### {_format_group(result.group)}",
        "",
        f"- Fit verdict: `{result.fit_verdict.status}`",
        f"- Confidence: {result.fit_verdict.confidence}",
        f"- Task count: {result.metrics.task_count}",
        f"- Success rate: {result.metrics.success_rate:.2f}",
        f"- Primary controls: {_format_controls(result.fit_verdict.primary_controls)}",
    ]
    if result.changes:
        changes = ", ".join(
            f"{change.field}: {change.from_value}->{change.to_value}"
            for change in result.changes
        )
        lines.append(f"- Suggested changes: {changes}")
    else:
        lines.append("- Suggested changes: none")
    lines.append("")
    return lines


def _format_group(group: dict[str, str]) -> str:
    if not group:
        return "Aggregate"
    return "Group: " + ", ".join(f"{field}={value}" for field, value in group.items())
