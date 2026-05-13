from __future__ import annotations

from dataclasses import asdict, dataclass

from adaharness.analysis.diagnostic_config import DiagnosticConfig
from adaharness.analysis.metrics import TraceMetrics


@dataclass(frozen=True)
class DiagnosticSignal:
    kind: str
    control: str
    severity: str
    message: str
    evidence: tuple[str, ...]
    rule: str = ""
    evidence_count: int = 0
    confidence: str = "low"
    missing_data: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "missing_data", tuple(self.missing_data))

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def diagnose_harness(
    metrics: TraceMetrics,
    *,
    config: DiagnosticConfig | None = None,
) -> tuple[DiagnosticSignal, ...]:
    diagnostic_config = config or DiagnosticConfig()
    signals: list[DiagnosticSignal] = []
    signals.extend(_overconstraint_signals(metrics, diagnostic_config))
    signals.extend(_underconstraint_signals(metrics, diagnostic_config))
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
                rule="no configured diagnostic rule matched",
                evidence_count=metrics.task_count,
                confidence=_confidence(metrics.task_count, diagnostic_config),
                missing_data=_missing_data(metrics, control="harness"),
            )
        )
    return tuple(signals)


def _overconstraint_signals(
    metrics: TraceMetrics,
    config: DiagnosticConfig,
) -> list[DiagnosticSignal]:
    signals = []
    verifier = config.verifier_overconstraint
    if (
        metrics.verifier_events >= verifier.min_events
        and metrics.verifier_catch_rate < verifier.max_catch_rate
        and metrics.verifier_cost_share >= verifier.min_cost_share
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
                rule=(
                    f"verifier_events >= {verifier.min_events} and "
                    f"verifier_catch_rate < {verifier.max_catch_rate:.2f} and "
                    f"verifier_cost_share >= {verifier.min_cost_share:.2f}"
                ),
                evidence_count=metrics.verifier_events,
                confidence=_confidence(metrics.verifier_events, config),
                missing_data=_missing_data(metrics, control="verification_control"),
            )
        )
    planner = config.planner_overconstraint
    if (
        metrics.planner_events >= planner.min_events
        and metrics.planner_latency_share >= planner.min_latency_share
        and metrics.success_rate >= planner.min_success_rate
    ):
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
                rule=(
                    f"planner_events >= {planner.min_events} and "
                    f"planner_latency_share >= {planner.min_latency_share:.2f} and "
                    f"success_rate >= {planner.min_success_rate:.2f}"
                ),
                evidence_count=metrics.planner_events,
                confidence=_confidence(metrics.planner_events, config),
                missing_data=_missing_data(metrics, control="planning_control"),
            )
        )
    retry = config.retry_overconstraint
    if metrics.retry_events >= retry.min_events and metrics.retry_success_rate < retry.max_success_rate:
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
                rule=(
                    f"retry_events >= {retry.min_events} and "
                    f"retry_success_rate < {retry.max_success_rate:.2f}"
                ),
                evidence_count=metrics.retry_events,
                confidence=_confidence(metrics.retry_events, config),
                missing_data=_missing_data(metrics, control="retry_control"),
            )
        )
    return signals


def _underconstraint_signals(
    metrics: TraceMetrics,
    config: DiagnosticConfig,
) -> list[DiagnosticSignal]:
    signals = []
    tool_failure = config.tool_failure
    if (
        metrics.tool_call_count >= tool_failure.min_tool_calls
        and metrics.tool_failure_rate >= tool_failure.min_failure_rate
    ):
        signals.append(
            DiagnosticSignal(
                kind="underconstraint",
                control="tool_control",
                severity="high",
                message="Tool failures are frequent enough to justify stronger tool control.",
                evidence=(f"tool_failure_rate={metrics.tool_failure_rate:.2f}",),
                rule=(
                    f"tool_call_count >= {tool_failure.min_tool_calls} and "
                    f"tool_failure_rate >= {tool_failure.min_failure_rate:.2f}"
                ),
                evidence_count=metrics.tool_call_count,
                confidence=_confidence(metrics.tool_call_count, config),
                missing_data=_missing_data(metrics, control="tool_control"),
            )
        )
    ignored = config.tool_result_ignored
    if (
        metrics.tool_call_count >= ignored.min_tool_calls
        and metrics.tool_result_ignored_rate >= ignored.min_ignored_rate
    ):
        signals.append(
            DiagnosticSignal(
                kind="underconstraint",
                control="tool_control",
                severity="high",
                message="The agent appears to ignore tool results.",
                evidence=(f"tool_result_ignored_rate={metrics.tool_result_ignored_rate:.2f}",),
                rule=(
                    f"tool_call_count >= {ignored.min_tool_calls} and "
                    f"tool_result_ignored_rate >= {ignored.min_ignored_rate:.2f}"
                ),
                evidence_count=metrics.tool_call_count,
                confidence=_confidence(metrics.tool_call_count, config),
                missing_data=_missing_data(metrics, control="tool_control"),
            )
        )
    missing_verifier = config.missing_verifier
    if (
        metrics.final_count >= missing_verifier.min_final_events
        and metrics.failure_rate >= missing_verifier.min_failure_rate
        and metrics.verifier_events == 0
    ):
        signals.append(
            DiagnosticSignal(
                kind="underconstraint",
                control="verification_control",
                severity="medium",
                message="Failures are present but no verifier events were recorded.",
                evidence=(f"failure_rate={metrics.failure_rate:.2f}",),
                rule=(
                    f"final_count >= {missing_verifier.min_final_events} and "
                    f"failure_rate >= {missing_verifier.min_failure_rate:.2f} and "
                    "verifier_events == 0"
                ),
                evidence_count=metrics.final_count,
                confidence=_confidence(metrics.final_count, config),
                missing_data=_missing_data(metrics, control="verification_control"),
            )
        )
    missing_retry = config.missing_retry
    if (
        metrics.final_count >= missing_retry.min_final_events
        and metrics.failure_rate >= missing_retry.min_failure_rate
        and metrics.failed_without_retry_rate >= missing_retry.min_failed_without_retry_rate
    ):
        signals.append(
            DiagnosticSignal(
                kind="underconstraint",
                control="retry_control",
                severity="medium",
                message="Many failed tasks ended without retry.",
                evidence=(f"failed_without_retry_rate={metrics.failed_without_retry_rate:.2f}",),
                rule=(
                    f"final_count >= {missing_retry.min_final_events} and "
                    f"failure_rate >= {missing_retry.min_failure_rate:.2f} and "
                    "failed_without_retry_rate >= "
                    f"{missing_retry.min_failed_without_retry_rate:.2f}"
                ),
                evidence_count=metrics.final_count,
                confidence=_confidence(metrics.final_count, config),
                missing_data=_missing_data(metrics, control="retry_control"),
            )
        )
    return signals


def _confidence(evidence_count: int, config: DiagnosticConfig) -> str:
    if evidence_count >= config.confidence.high_evidence_count:
        return "high"
    if evidence_count >= config.confidence.medium_evidence_count:
        return "medium"
    return "low"


def _missing_data(metrics: TraceMetrics, *, control: str) -> tuple[str, ...]:
    missing = []
    if metrics.final_count < metrics.task_count:
        missing.append("final_outcome")
    if control == "verification_control" and metrics.total_cost <= 0:
        missing.append("cost")
    if control == "planning_control" and metrics.total_latency_ms <= 0:
        missing.append("latency")
    return tuple(missing)
