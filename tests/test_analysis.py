import unittest

from adaharness.analysis import (
    TraceEvent,
    compute_trace_metrics,
    diagnose_harness,
    recommend_policy_changes,
    render_analysis_report,
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
