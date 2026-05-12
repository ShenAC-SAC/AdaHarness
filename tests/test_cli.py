from adaharness.cli import main
from adaharness.profiler.profile_schema import ModelProfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def test_compare_cli_runs(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(["compare", "--model", "example-model", "--taskset", "tasks/eval"])

        self.assertEqual(exit_code, 0)
        self.assertIn('"model_name": "example-model"', output.getvalue())
        self.assertIn('"harness_name": "adaptive"', output.getvalue())
        self.assertIn('"runs"', output.getvalue())

    def test_compare_cli_supports_model_matrix(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(
                [
                    "compare",
                    "--models",
                    "small-sim,strong-sim",
                    "--harnesses",
                    "bare,structured,adaptive",
                    "--taskset",
                    "tasks/eval",
                ]
            )

        data = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(data["comparisons"]), 2)
        self.assertEqual(len(data["comparisons"][0]["results"]), 3)

    def test_profile_accepts_provider_options(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(["profile", "--provider", "mock", "--model", "mock-model"])

        data = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(data["model_name"], "mock-model")

    def test_profile_accepts_profiler_taskset(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(
                ["profile", "--provider", "mock", "--model", "mock-model", "--taskset", "tasks/profiler"]
            )

        data = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertIn("scores", data)
        self.assertIn("recommended_controls", data)

    def test_recommend_writes_reusable_policy_artifact(self) -> None:
        profile = ModelProfile(
            model_name="artifact-model",
            planning=0.65,
            tool_use=0.65,
            instruction_following=0.65,
            self_verification=0.65,
            context_management=0.65,
            recovery=0.65,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            policy_path = Path(tmpdir) / "policy.json"
            profile_path.write_text(json.dumps(profile.to_dict()), encoding="utf-8")

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "recommend",
                        "--profile",
                        str(profile_path),
                        "--risk",
                        "high",
                        "--budget",
                        "constrained",
                        "--out",
                        str(policy_path),
                    ]
                )

            stdout_data = json.loads(output.getvalue())
            file_data = json.loads(policy_path.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout_data, file_data)
            self.assertEqual(file_data["schema_version"], "0.2")
            self.assertEqual(file_data["risk"], "high")
            self.assertEqual(file_data["budget"], "constrained")
            self.assertEqual(file_data["policy"]["verifier_strength"], "selective")

    def test_assemble_compiles_policy_artifact(self) -> None:
        profile = ModelProfile(
            model_name="assemble-model",
            planning=0.65,
            tool_use=0.65,
            instruction_following=0.65,
            self_verification=0.65,
            context_management=0.65,
            recovery=0.65,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            policy_path = Path(tmpdir) / "policy.json"
            spec_path = Path(tmpdir) / "harness-spec.json"
            profile_path.write_text(json.dumps(profile.to_dict()), encoding="utf-8")

            with redirect_stdout(StringIO()):
                main(["recommend", "--profile", str(profile_path), "--out", str(policy_path)])

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "assemble",
                        "--policy",
                        str(policy_path),
                        "--name",
                        "test_spec",
                        "--out",
                        str(spec_path),
                    ]
                )

            stdout_data = json.loads(output.getvalue())
            file_data = json.loads(spec_path.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout_data, file_data)
            self.assertEqual(file_data["schema_version"], "0.3")
            self.assertEqual(file_data["name"], "test_spec")
            self.assertIn("planner", file_data["enabled_modules"])
            self.assertEqual(file_data["metadata"]["recommendation"]["model_name"], "assemble-model")
