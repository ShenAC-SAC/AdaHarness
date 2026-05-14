from __future__ import annotations

from dataclasses import dataclass, field

from adaharness.analysis.diagnostics import DiagnosticSignal
from adaharness.analysis.fit import FitVerdict
from adaharness.analysis.metrics import TraceMetrics
from adaharness.analysis.policy_diff import PolicyChange
from adaharness.analysis.validation import TraceValidationWarning


@dataclass(frozen=True)
class AnalysisResult:
    metrics: TraceMetrics
    fit_verdict: FitVerdict
    trace_warnings: tuple[TraceValidationWarning, ...]
    signals: tuple[DiagnosticSignal, ...]
    changes: tuple[PolicyChange, ...]
    group: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace_warnings", tuple(self.trace_warnings))
        object.__setattr__(self, "signals", tuple(self.signals))
        object.__setattr__(self, "changes", tuple(self.changes))
        object.__setattr__(self, "group", dict(self.group))

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "metrics": self.metrics.to_dict(),
            "fit_verdict": self.fit_verdict.to_dict(),
            "trace_warnings": [warning.to_dict() for warning in self.trace_warnings],
            "diagnosis": {"signals": [signal.to_dict() for signal in self.signals]},
            "policy_diff": {"changes": [change.to_dict() for change in self.changes]},
        }
        if self.group:
            data["group"] = dict(self.group)
        return data
