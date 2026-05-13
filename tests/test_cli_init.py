from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from adaharness.cli import main


class InitCliTests(unittest.TestCase):
    def test_init_writes_starter_files_without_repo_examples(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / ".adaharness"
            output = StringIO()

            with redirect_stdout(output):
                exit_code = main(["init", "--path", str(root)])

            data = json.loads(output.getvalue())

            self.assertEqual(exit_code, 0)
            self.assertEqual(data["path"], str(root))
            self.assertIn("Starter files", data["purpose"])
            self.assertIn("capture", data["capture_command"])
            self.assertIn("example_command", data)
            self.assertTrue((root / "README.md").exists())
            self.assertTrue((root / "diagnostics" / "default.toml").exists())
            self.assertTrue((root / "policies" / "current-policy.json").exists())
            self.assertTrue((root / "tasks" / "connectivity-smoke.jsonl").exists())
            self.assertTrue((root / "tasks" / "ifeval-lite.jsonl").exists())
            self.assertTrue((root / "traces" / "overconstrained_harness.jsonl").exists())
            self.assertTrue((root / "traces" / "undercontrolled_tool_use.jsonl").exists())
            self.assertTrue((root / "reports").is_dir())

            with redirect_stdout(StringIO()):
                analyze_exit_code = main(
                    [
                        "analyze",
                        "--traces",
                        str(root / "traces" / "overconstrained_harness.jsonl"),
                        "--current-policy",
                        str(root / "policies" / "current-policy.json"),
                        "--diagnostics-config",
                        str(root / "diagnostics" / "default.toml"),
                        "--out",
                        str(root / "reports" / "harness-drift.md"),
                    ]
                )

            self.assertEqual(analyze_exit_code, 0)
            self.assertTrue((root / "reports" / "harness-drift.md").exists())

    def test_init_does_not_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / ".adaharness"
            with redirect_stdout(StringIO()):
                main(["init", "--path", str(root)])
            policy_path = root / "policies" / "current-policy.json"
            policy_path.write_text('{"custom": true}\n', encoding="utf-8")

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(["init", "--path", str(root)])
            data = json.loads(output.getvalue())

            self.assertEqual(exit_code, 0)
            self.assertIn(str(policy_path), data["skipped"])
            self.assertEqual(policy_path.read_text(encoding="utf-8"), '{"custom": true}\n')
