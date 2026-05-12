from __future__ import annotations

from adaharness.analysis.diagnostics import DiagnosticSignal
from adaharness.analysis.metrics import TraceMetrics
from adaharness.analysis.policy_diff import PolicyChange


def render_analysis_report(
    *,
    metrics: TraceMetrics,
    signals: tuple[DiagnosticSignal, ...],
    changes: tuple[PolicyChange, ...],
) -> str:
    lines = [
        "# AdaHarness Drift Report",
        "",
        "## Summary",
        "",
        f"- Task count: {metrics.task_count}",
        f"- Success rate: {metrics.success_rate:.2f}",
        f"- Total cost: {metrics.total_cost:.4f}",
        f"- Total latency ms: {metrics.total_latency_ms:.0f}",
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
    for signal in signals:
        lines.append(f"- **{signal.kind} / {signal.control} / {signal.severity}**: {signal.message}")
        for item in signal.evidence:
            lines.append(f"  - {item}")
    lines.extend(["", "## Suggested Policy Diff", ""])
    if not changes:
        lines.append("- No policy change suggested from current evidence.")
    for change in changes:
        lines.append(
            f"- `{change.field}`: `{change.from_value}` -> `{change.to_value}`"
        )
        lines.append(f"  - Reason: {change.reason}")
        for item in change.evidence:
            lines.append(f"  - Evidence: {item}")
    return "\n".join(lines)
