from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import tempfile
import unittest

from adaharness.cli import main


class AnalyzeCliTests(unittest.TestCase):
    def test_analyze_writes_report_and_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            trace_path = root / "trace.jsonl"
            policy_path = root / "policy.json"
            report_path = root / "report.md"
            trace_path.write_text(
                "\n".join(
                    json.dumps(event)
                    for event in [
                        {"task_id": "t1", "event": "verifier", "status": "pass", "cost": 0.01},
                        {"task_id": "t1", "event": "final", "success": True, "cost": 0.02},
                        {"task_id": "t2", "event": "verifier", "status": "pass", "cost": 0.01},
                        {"task_id": "t2", "event": "final", "success": True, "cost": 0.02},
                        {"task_id": "t3", "event": "verifier", "status": "pass", "cost": 0.01},
                        {"task_id": "t3", "event": "final", "success": True, "cost": 0.02},
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            policy_path.write_text(
                json.dumps({"verification_control": "always"}),
                encoding="utf-8",
            )

            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "analyze",
                        "--traces",
                        str(trace_path),
                        "--current-policy",
                        str(policy_path),
                        "--out",
                        str(report_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(report_path.exists())
            self.assertTrue(report_path.with_suffix(".analysis.json").exists())
            self.assertTrue(report_path.with_suffix(".metrics.json").exists())
            self.assertTrue(report_path.with_suffix(".diagnosis.json").exists())
            self.assertTrue(report_path.with_suffix(".policy-diff.json").exists())
            analysis = json.loads(report_path.with_suffix(".analysis.json").read_text(encoding="utf-8"))
            self.assertIn("metrics", analysis)
            self.assertIn("diagnosis", analysis)
            self.assertIn("policy_diff", analysis)
            policy_diff = json.loads(report_path.with_suffix(".policy-diff.json").read_text(encoding="utf-8"))
            self.assertEqual(policy_diff["changes"][0]["field"], "verification_control")
