import json
from pathlib import Path
import tempfile
import unittest

from adaharness.analysis import compute_trace_metrics, load_trace_events, validate_trace_events
from adaharness.trace import TraceRecorder


class TraceRecorderTests(unittest.TestCase):
    def test_records_jsonl_events_that_analysis_can_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces" / "run.jsonl"
            recorder = TraceRecorder(path, model="gpt-example", policy="current")
            trace = recorder.task("task-1")

            trace.planner(latency_ms=25)
            trace.verifier(status="pass", cost=0.001)
            trace.tool_call(tool="search_docs", status="success", latency_ms=100)
            trace.final(success=True, cost=0.010, latency_ms=500, task_type="support")

            events = load_trace_events([path])
            metrics = compute_trace_metrics(events)
            warnings = validate_trace_events(events)

        self.assertEqual(len(events), 4)
        self.assertEqual(events[0].model, "gpt-example")
        self.assertEqual(events[0].policy, "current")
        self.assertEqual(metrics.success_rate, 1.0)
        self.assertEqual(events[-1].task_type, "support")
        self.assertEqual(metrics.tool_call_count, 1)
        self.assertEqual(warnings, ())

    def test_task_defaults_override_recorder_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "run.jsonl"
            recorder = TraceRecorder(path, model="default-model", policy="default-policy")
            trace = recorder.task("task-1", model="task-model", policy="task-policy")

            trace.final(success=True)

            record = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(record["schema_version"], "0.1")
        self.assertEqual(record["model"], "task-model")
        self.assertEqual(record["policy"], "task-policy")

    def test_timed_span_records_failure_and_reraises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "run.jsonl"
            trace = TraceRecorder(path).task("task-1")

            with self.assertRaises(RuntimeError):
                with trace.timed("tool_call", tool="search_docs"):
                    raise RuntimeError("boom")

            record = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(record["event"], "tool_call")
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["reason"], "RuntimeError")
        self.assertIn("latency_ms", record)
