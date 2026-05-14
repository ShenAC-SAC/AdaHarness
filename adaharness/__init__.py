"""Trace-first harness drift analysis for LLM agent projects."""

from adaharness.analysis import (
    DiagnosticConfig,
    DiagnosticSignal,
    FitVerdict,
    GROUP_FIELDS,
    PolicyChange,
    TraceEventGroup,
    TraceEvent,
    TraceMetrics,
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
from adaharness.api import analyze_traces
from adaharness.trace import TaskTrace, TraceRecorder, TraceSpan

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "analyze_traces",
    "DiagnosticConfig",
    "DiagnosticSignal",
    "FitVerdict",
    "GROUP_FIELDS",
    "PolicyChange",
    "TaskTrace",
    "TraceEvent",
    "TraceEventGroup",
    "TraceMetrics",
    "TraceRecorder",
    "TraceSpan",
    "TraceValidationWarning",
    "assess_harness_fit",
    "compute_trace_metrics",
    "diagnose_harness",
    "group_trace_events",
    "load_diagnostic_config",
    "load_trace_events",
    "mixed_group_warnings",
    "normalize_group_by",
    "recommend_policy_changes",
    "render_analysis_report",
    "validate_trace_events",
]
