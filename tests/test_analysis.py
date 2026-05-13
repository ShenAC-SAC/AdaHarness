import unittest

from adaharness.analysis import (
    TraceEvent,
    compute_trace_metrics,
    diagnose_harness,
    load_diagnostic_config,
    recommend_policy_changes,
    render_analysis_report,
    validate_trace_events,
)


class AnalysisTests(unittest.TestCase):
    def test_overconstraint_signals_recommend_weaker_controls(self) -> None:
        events = []
        for index in range(5):
            task_id = f"t{index}"
            events.extend(
                [
                    TraceEvent(task_id=task_id, event="planner", latency_ms=400),
                    TraceEvent(task_id=task_id, event="verifier", status="pass", cost=0.01),
                    TraceEvent(task_id=task_id, event="final", success=True, cost=0.03, latency_ms=1000),
                ]
            )

        metrics = compute_trace_metrics(tuple(events))
        signals = diagnose_harness(metrics)
        changes = recommend_policy_changes(
            signals,
            current_policy={
                "planning_control": "explicit",
                "verification_control": "always",
            },
        )

        self.assertEqual(metrics.success_rate, 1.0)
        self.assertGreater(metrics.verifier_cost_share, 0.2)
        self.assertIn("verification_control", [signal.control for signal in signals])
        self.assertIn("planning_control", [signal.control for signal in signals])
        self.assertIn(
            {
                "confidence": "low",
                "evidence_count": 5,
                "field": "verification_control",
                "from": "always",
                "to": "selective",
                "reason": "Verifier appears expensive but rarely catches failures.",
                "evidence": ("verifier_catch_rate=0.00", "verifier_cost_share=0.25"),
            },
            [change.to_dict() for change in changes],
        )

    def test_underconstraint_signals_recommend_stronger_controls(self) -> None:
        events = (
            TraceEvent(task_id="t1", event="tool_call", status="failed"),
            TraceEvent(task_id="t1", event="final", success=False),
            TraceEvent(task_id="t2", event="tool_call", status="success"),
            TraceEvent(task_id="t2", event="tool_result_ignored"),
            TraceEvent(task_id="t2", event="final", success=False),
        )

        metrics = compute_trace_metrics(events)
        signals = diagnose_harness(metrics)
        changes = recommend_policy_changes(
            signals,
            current_policy={
                "tool_control": "none",
                "retry_control": "none",
                "verification_control": "off",
            },
        )
        report = render_analysis_report(metrics=metrics, signals=signals, changes=changes)

        self.assertGreater(metrics.tool_failure_rate, 0.0)
        self.assertIn("tool_control", [signal.control for signal in signals])
        self.assertIn("retry_control", [change.field for change in changes])
        self.assertIn("AdaHarness Drift Report", report)

    def test_ignored_tool_result_without_tool_call_still_signals_underconstraint(self) -> None:
        events = (
            TraceEvent(task_id="t1", event="tool_result_ignored"),
            TraceEvent(task_id="t1", event="final", success=False),
        )

        metrics = compute_trace_metrics(events)
        signals = diagnose_harness(metrics)

        self.assertEqual(metrics.tool_call_count, 0)
        self.assertEqual(metrics.tool_result_ignored_count, 1)
        self.assertEqual(metrics.tool_result_ignored_rate, 1.0)
        self.assertIn(
            "tool_control",
            [signal.control for signal in signals if signal.kind == "underconstraint"],
        )

    def test_trace_validation_reports_unknown_events_and_missing_final(self) -> None:
        warnings = validate_trace_events(
            (
                TraceEvent(task_id="t1", event="unknown_event"),
                TraceEvent(task_id="t2", event="final", success=True),
                TraceEvent(task_id="t2", event="final", success=True),
            )
        )

        codes = [warning.code for warning in warnings]
        self.assertIn("unknown_event", codes)
        self.assertIn("missing_final", codes)
        self.assertIn("multiple_final", codes)
        self.assertIn("missing_cost", codes)
        self.assertIn("missing_latency", codes)

    def test_trace_validation_reports_control_specific_missing_evidence(self) -> None:
        warnings = validate_trace_events(
            (
                TraceEvent(task_id="t1", event="verifier"),
                TraceEvent(task_id="t1", event="planner"),
                TraceEvent(task_id="t1", event="tool_result_ignored"),
                TraceEvent(task_id="t1", event="final", success=True, cost=0.01, latency_ms=100),
            )
        )

        codes = [warning.code for warning in warnings]
        self.assertIn("missing_verifier_cost", codes)
        self.assertIn("missing_planner_latency", codes)
        self.assertIn("missing_tool_call_denominator", codes)

    def test_diagnostic_thresholds_can_be_loaded_from_toml(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "diagnostics.toml"
            config_path.write_text(
                "\n".join(
                    [
                        "[diagnostics.verifier_overconstraint]",
                        "min_events = 50",
                        "max_catch_rate = 0.02",
                        "min_cost_share = 0.30",
                    ]
                ),
                encoding="utf-8",
            )

            config = load_diagnostic_config(config_path)

        self.assertEqual(config.verifier_overconstraint.min_events, 50)
        self.assertEqual(config.verifier_overconstraint.max_catch_rate, 0.02)
        self.assertEqual(config.verifier_overconstraint.min_cost_share, 0.30)
