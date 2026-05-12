from __future__ import annotations

from dataclasses import asdict, dataclass

from adaharness.analysis.metrics import TraceMetrics


@dataclass(frozen=True)
class DiagnosticSignal:
    kind: str
    control: str
    severity: str
    message: str
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", tuple(self.evidence))

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def diagnose_harness(metrics: TraceMetrics) -> tuple[DiagnosticSignal, ...]:
    signals: list[DiagnosticSignal] = []
    signals.extend(_overconstraint_signals(metrics))
    signals.extend(_underconstraint_signals(metrics))
    if not signals:
        signals.append(
            DiagnosticSignal(
                kind="balanced",
                control="harness",
                severity="low",
                message="No strong overconstraint or underconstraint signal was detected.",
                evidence=(
                    f"success_rate={metrics.success_rate:.2f}",
                    f"task_count={metrics.task_count}",
                ),
            )
        )
    return tuple(signals)


def _overconstraint_signals(metrics: TraceMetrics) -> list[DiagnosticSignal]:
    signals = []
    if (
        metrics.verifier_events >= 3
        and metrics.verifier_catch_rate < 0.05
        and metrics.verifier_cost_share >= 0.20
    ):
        signals.append(
            DiagnosticSignal(
                kind="overconstraint",
                control="verification_control",
                severity="high",
                message="Verifier appears expensive but rarely catches failures.",
                evidence=(
                    f"verifier_catch_rate={metrics.verifier_catch_rate:.2f}",
                    f"verifier_cost_share={metrics.verifier_cost_share:.2f}",
                ),
            )
        )
    if metrics.planner_events >= 3 and metrics.planner_latency_share >= 0.25 and metrics.success_rate >= 0.80:
        signals.append(
            DiagnosticSignal(
                kind="overconstraint",
                control="planning_control",
                severity="medium",
                message="Planning adds substantial latency while overall success is already high.",
                evidence=(
                    f"planner_latency_share={metrics.planner_latency_share:.2f}",
                    f"success_rate={metrics.success_rate:.2f}",
                ),
            )
        )
    if metrics.retry_events >= 3 and metrics.retry_success_rate < 0.20:
        signals.append(
            DiagnosticSignal(
                kind="overconstraint",
                control="retry_control",
                severity="medium",
                message="Retries are common but rarely lead to successful task outcomes.",
                evidence=(
                    f"retry_events={metrics.retry_events}",
                    f"retry_success_rate={metrics.retry_success_rate:.2f}",
                ),
            )
        )
    return signals


def _underconstraint_signals(metrics: TraceMetrics) -> list[DiagnosticSignal]:
    signals = []
    if metrics.tool_failure_rate >= 0.15:
        signals.append(
            DiagnosticSignal(
                kind="underconstraint",
                control="tool_control",
                severity="high",
                message="Tool failures are frequent enough to justify stronger tool control.",
                evidence=(f"tool_failure_rate={metrics.tool_failure_rate:.2f}",),
            )
        )
    if metrics.tool_result_ignored_rate >= 0.05:
        signals.append(
            DiagnosticSignal(
                kind="underconstraint",
                control="tool_control",
                severity="high",
                message="The agent appears to ignore tool results.",
                evidence=(f"tool_result_ignored_rate={metrics.tool_result_ignored_rate:.2f}",),
            )
        )
    if metrics.failure_rate >= 0.15 and metrics.verifier_events == 0:
        signals.append(
            DiagnosticSignal(
                kind="underconstraint",
                control="verification_control",
                severity="medium",
                message="Failures are present but no verifier events were recorded.",
                evidence=(f"failure_rate={metrics.failure_rate:.2f}",),
            )
        )
    if metrics.failure_rate >= 0.15 and metrics.failed_without_retry_rate >= 0.50:
        signals.append(
            DiagnosticSignal(
                kind="underconstraint",
                control="retry_control",
                severity="medium",
                message="Many failed tasks ended without retry.",
                evidence=(f"failed_without_retry_rate={metrics.failed_without_retry_rate:.2f}",),
            )
        )
    return signals
