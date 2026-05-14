"""Trace-first harness drift analysis for LLM agent projects."""

from adaharness.analysis import (
    DiagnosticConfig,
    DiagnosticSignal,
    FitVerdict,
    PolicyChange,
    TraceEvent,
    TraceMetrics,
    TraceValidationWarning,
    assess_harness_fit,
    compute_trace_metrics,
    diagnose_harness,
    load_diagnostic_config,
    load_trace_events,
    recommend_policy_changes,
    render_analysis_report,
    validate_trace_events,
)
from adaharness.api import analyze_traces
from adaharness.trace import TaskTrace, TraceRecorder, TraceSpan

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "analyze_traces",
    "DiagnosticConfig",
    "DiagnosticSignal",
    "FitVerdict",
    "PolicyChange",
    "TaskTrace",
    "TraceEvent",
    "TraceMetrics",
    "TraceRecorder",
    "TraceSpan",
    "TraceValidationWarning",
    "assess_harness_fit",
    "compute_trace_metrics",
    "diagnose_harness",
    "load_diagnostic_config",
    "load_trace_events",
    "recommend_policy_changes",
    "render_analysis_report",
    "validate_trace_events",
]
