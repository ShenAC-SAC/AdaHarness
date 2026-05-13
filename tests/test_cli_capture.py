from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest

from adaharness.analysis import compute_trace_metrics, load_trace_events
from adaharness.cli import main


class CaptureCliTests(unittest.TestCase):
    def test_capture_lists_builtin_suites(self) -> None:
        output = StringIO()

        with redirect_stdout(output):
            exit_code = main(["capture", "--list-suites"])
        data = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(data["default"], "ifeval-lite")
        self.assertIn("connectivity-smoke", data["suites"])
        self.assertIn("ifeval-lite", data["suites"])

    def test_capture_runs_command_tasks_and_writes_analyzable_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            agent_path = root / "agent.py"
            tasks_path = root / "tasks.jsonl"
            trace_path = root / "run.jsonl"
            report_path = root / "report.md"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import json
                    import sys

                    prompt = sys.argv[1]
                    print("ADAHARNESS_EVENT " + json.dumps({
                        "event": "verifier",
                        "status": "pass",
                        "cost": 0.001,
                    }))
                    if "good" in prompt:
                        print("answer: OK")
                    else:
                        print("answer: not enough")
                    """
                ),
                encoding="utf-8",
            )
            tasks_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "task_id": "task-good",
                                "prompt": "good case",
                                "expected_contains": "OK",
                            }
                        ),
                        json.dumps(
                            {
                                "task_id": "task-bad",
                                "prompt": "bad case",
                                "expected_contains": "OK",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "capture",
                        "--tasks",
                        str(tasks_path),
                        "--out",
                        str(trace_path),
                        "--analyze-out",
                        str(report_path),
                        "--",
                        sys.executable,
                        str(agent_path),
                        "{prompt}",
                    ]
                )
            summary = json.loads(output.getvalue())
            events = load_trace_events([trace_path])
            metrics = compute_trace_metrics(events)

            self.assertEqual(exit_code, 0)
            self.assertEqual(summary["task_count"], 2)
            self.assertEqual(summary["success_count"], 1)
            self.assertEqual(summary["failure_count"], 1)
            self.assertTrue(report_path.exists())
            self.assertTrue(report_path.with_suffix(".analysis.json").exists())
            self.assertEqual(metrics.task_count, 2)
            self.assertEqual(metrics.final_count, 2)
            self.assertEqual(metrics.verifier_events, 2)
            self.assertEqual(metrics.success_rate, 0.5)

    def test_capture_uses_builtin_suite_when_tasks_are_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            agent_path = root / "agent.py"
            trace_path = root / "run.jsonl"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import json
                    import sys

                    prompt = sys.argv[1]
                    if "valid JSON" in prompt:
                        answer = json.dumps({"status": "ok", "value": 7})
                    elif "three comma-separated words" in prompt:
                        answer = "trace, policy, harness"
                    elif "uppercase" in prompt:
                        answer = "CALIBRATED"
                    elif "one lowercase word" in prompt:
                        answer = "traces"
                    elif "Do not use the word" in prompt:
                        answer = "AdaHarness analyzes traces."
                    else:
                        answer = "ADAHARNESS_OK"
                    print(answer)
                    """
                ),
                encoding="utf-8",
            )

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "capture",
                        "--out",
                        str(trace_path),
                        "--",
                        sys.executable,
                        str(agent_path),
                        "{prompt}",
                    ]
                )
            summary = json.loads(output.getvalue())
            metrics = compute_trace_metrics(load_trace_events([trace_path]))

            self.assertEqual(exit_code, 0)
            self.assertEqual(summary["task_count"], 6)
            self.assertEqual(summary["success_count"], 6)
            self.assertEqual(metrics.success_rate, 1.0)

    def test_capture_supports_connectivity_smoke_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            agent_path = root / "agent.py"
            trace_path = root / "run.jsonl"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import sys

                    prompt = sys.argv[1]
                    print("READY" if "READY" in prompt else "ADAHARNESS_OK")
                    """
                ),
                encoding="utf-8",
            )

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "capture",
                        "--suite",
                        "connectivity-smoke",
                        "--out",
                        str(trace_path),
                        "--",
                        sys.executable,
                        str(agent_path),
                        "{prompt}",
                    ]
                )
            summary = json.loads(output.getvalue())

            self.assertEqual(exit_code, 0)
            self.assertEqual(summary["task_count"], 2)
            self.assertEqual(summary["success_count"], 2)
