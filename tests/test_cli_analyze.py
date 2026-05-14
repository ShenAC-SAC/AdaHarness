from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import tempfile
import unittest

from adaharness.cli import main


class AnalyzeCliTests(unittest.TestCase):
    def test_help_exposes_only_analyze_command(self) -> None:
        output = StringIO()

        with self.assertRaises(SystemExit) as context:
            with redirect_stdout(output):
                main(["--help"])

        self.assertEqual(context.exception.code, 0)
        help_text = output.getvalue()
        self.assertIn("{analyze}", help_text)
        self.assertNotIn("capture", help_text)
        self.assertNotIn("calibrate", help_text)

    def test_analyze_writes_report_and_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            trace_path = root / "trace.jsonl"
            policy_path = root / "policy.json"
            report_path = root / "report.md"
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
            self.assertIn("diagnostics_config", analysis)
            self.assertIn("metrics", analysis)
            self.assertIn("fit_verdict", analysis)
            self.assertIn("trace_warnings", analysis)
            self.assertIn("diagnosis", analysis)
            self.assertIn("policy_diff", analysis)
            self.assertEqual(analysis["fit_verdict"]["status"], "likely_overcontrolled")
            diagnosis = json.loads(report_path.with_suffix(".diagnosis.json").read_text(encoding="utf-8"))
            self.assertIn("fit_verdict", diagnosis)
            policy_diff = json.loads(report_path.with_suffix(".policy-diff.json").read_text(encoding="utf-8"))
            self.assertEqual(policy_diff["changes"][0]["field"], "verification_control")
            self.assertEqual(policy_diff["changes"][0]["confidence"], "low")
