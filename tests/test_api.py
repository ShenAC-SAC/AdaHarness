from pathlib import Path
import json
import tempfile
import unittest

from adaharness import TraceRecorder, analyze_traces


class PublicApiTests(unittest.TestCase):
    def test_analyze_traces_returns_report_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            trace_path = root / "trace.jsonl"
            policy_path = root / "policy.json"
            trace_path.write_text(
                "\n".join(
                    json.dumps(event)
                    for task_id in ["t1", "t2", "t3", "t4", "t5"]
                    for event in [
                        {"task_id": task_id, "event": "verifier", "status": "pass", "cost": 0.01},
                        {"task_id": task_id, "event": "final", "success": True, "cost": 0.02},
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            policy_path.write_text(json.dumps({"verification_control": "always"}), encoding="utf-8")

            data = analyze_traces([trace_path], current_policy=policy_path)

        self.assertIn("AdaHarness Drift Report", data["report"])
        self.assertEqual(data["metrics"]["task_count"], 5)
        self.assertEqual(data["policy_diff"]["changes"][0]["field"], "verification_control")
        self.assertEqual(data["policy_diff"]["changes"][0]["from"], "always")
        self.assertEqual(data["policy_diff"]["changes"][0]["to"], "selective")

    def test_top_level_exports_trace_recorder(self) -> None:
        self.assertIs(TraceRecorder, TraceRecorder)
