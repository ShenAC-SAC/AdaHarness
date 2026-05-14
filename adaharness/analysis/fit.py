from __future__ import annotations

from dataclasses import asdict, dataclass

from adaharness.analysis.diagnostics import DiagnosticSignal
from adaharness.analysis.metrics import TraceMetrics
from adaharness.analysis.validation import TraceValidationWarning


@dataclass(frozen=True)
class FitVerdict:
    status: str
    confidence: str
    summary: str
    primary_controls: tuple[str, ...]
    evidence: tuple[str, ...]
    evidence_count: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "primary_controls", tuple(self.primary_controls))
        object.__setattr__(self, "evidence", tuple(self.evidence))

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def assess_harness_fit(
    *,
    metrics: TraceMetrics,
    signals: tuple[DiagnosticSignal, ...],
    trace_warnings: tuple[TraceValidationWarning, ...] = (),
) -> FitVerdict:
    """Summarize observational diagnostics into a model-harness fit verdict."""

    if metrics.final_count == 0:
        return FitVerdict(
            status="insufficient_evidence",
            confidence="low",
            summary="No final outcomes were recorded, so model-harness fit cannot be assessed.",
            primary_controls=(),
            evidence=(f"final_count={metrics.final_count}", f"task_count={metrics.task_count}"),
            evidence_count=metrics.final_count,
        )

    overcontrolled = tuple(signal for signal in signals if signal.kind == "overconstraint")
    undercontrolled = tuple(signal for signal in signals if signal.kind == "underconstraint")
    if overcontrolled and undercontrolled:
        supporting = overcontrolled + undercontrolled
        return FitVerdict(
            status="mixed_signals",
            confidence=_strongest_confidence(supporting),
            summary=(
                "Overconstraint and underconstraint signals both appeared; segment traces before "
                "making broad harness changes."
            ),
            primary_controls=_primary_controls(supporting),
            evidence=_signal_evidence(supporting),
            evidence_count=_evidence_count(supporting),
        )
    if overcontrolled:
        return FitVerdict(
            status="likely_overcontrolled",
            confidence=_strongest_confidence(overcontrolled),
            summary="Harness controls appear heavier than current trace evidence justifies.",
            primary_controls=_primary_controls(overcontrolled),
            evidence=_signal_evidence(overcontrolled),
            evidence_count=_evidence_count(overcontrolled),
        )
    if undercontrolled:
        return FitVerdict(
            status="likely_undercontrolled",
            confidence=_strongest_confidence(undercontrolled),
            summary="Current traces show failure modes that may need stronger harness control.",
            primary_controls=_primary_controls(undercontrolled),
            evidence=_signal_evidence(undercontrolled),
            evidence_count=_evidence_count(undercontrolled),
        )

    balanced = tuple(signal for signal in signals if signal.kind == "balanced")
    evidence = [f"success_rate={metrics.success_rate:.2f}", f"task_count={metrics.task_count}"]
    warning_codes = tuple(warning.code for warning in trace_warnings)
    if warning_codes:
        evidence.append("trace_warnings=" + ",".join(warning_codes[:5]))
    return FitVerdict(
        status="well_fit",
        confidence=_strongest_confidence(balanced) if balanced else "low",
        summary="No strong overconstraint or underconstraint signal was detected.",
        primary_controls=(),
        evidence=tuple(evidence),
        evidence_count=metrics.task_count,
    )


def _primary_controls(signals: tuple[DiagnosticSignal, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(signal.control for signal in signals if signal.control != "harness"))


def _signal_evidence(signals: tuple[DiagnosticSignal, ...]) -> tuple[str, ...]:
    evidence = []
    for signal in signals:
        evidence.append(f"{signal.control}: {signal.message}")
        evidence.extend(signal.evidence)
    return tuple(dict.fromkeys(evidence))


def _evidence_count(signals: tuple[DiagnosticSignal, ...]) -> int:
    return max((signal.evidence_count for signal in signals), default=0)


def _strongest_confidence(signals: tuple[DiagnosticSignal, ...]) -> str:
    ranking = {"low": 0, "medium": 1, "high": 2}
    strongest = "low"
    for signal in signals:
        if ranking.get(signal.confidence, 0) > ranking[strongest]:
            strongest = signal.confidence
    return strongest
