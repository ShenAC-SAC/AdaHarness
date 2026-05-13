from adaharness.cli import build_parser, main
from adaharness.profiler.profile_schema import ModelProfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def test_parser_exposes_primary_commands(self) -> None:
        help_text = build_parser().format_help()

        self.assertIn("init", help_text)
        self.assertIn("capture", help_text)
        self.assertIn("analyze", help_text)

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
            self.assertEqual(file_data["schema_version"], "0.5")
            self.assertEqual(file_data["name"], "test_spec")
            self.assertIn("planner", file_data["enabled_modules"])
            self.assertIn("planner", file_data["enabled_controllers"])
            self.assertIn("requirements", file_data)
            self.assertEqual(file_data["metadata"]["recommendation"]["model_name"], "assemble-model")

    def test_run_records_enabled_modules_from_harness_spec(self) -> None:
        profile = ModelProfile(
            model_name="run-model",
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
            run_path = Path(tmpdir) / "run.json"
            profile_path.write_text(json.dumps(profile.to_dict()), encoding="utf-8")

            with redirect_stdout(StringIO()):
                main(["recommend", "--profile", str(profile_path), "--out", str(policy_path)])
                main(["assemble", "--policy", str(policy_path), "--out", str(spec_path)])

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "run",
                        "--harness-spec",
                        str(spec_path),
                        "--task",
                        "tasks/eval",
                        "--provider",
                        "mock",
                        "--model",
                        "mock-model",
                        "--out",
                        str(run_path),
                    ]
                )

            data = json.loads(output.getvalue())
            events = data["runs"][0]["trace"]["events"]
            enabled_modules = [
                event["payload"]["module"]
                for event in events
                if event["event_type"] == "module_enabled"
            ]
            self.assertEqual(exit_code, 0)
            self.assertIn("trace", enabled_modules)
            self.assertIn("planner", enabled_modules)
            self.assertIn("trace_path", data["runs"][0])

    def test_migrate_outputs_policy_and_module_diff(self) -> None:
        old_profile = ModelProfile(
            model_name="old-small",
            planning=0.35,
            tool_use=0.35,
            instruction_following=0.35,
            self_verification=0.35,
            context_management=0.35,
            recovery=0.35,
        )
        new_profile = ModelProfile(
            model_name="new-strong",
            planning=0.9,
            tool_use=0.9,
            instruction_following=0.9,
            self_verification=0.9,
            context_management=0.9,
            recovery=0.9,
            cost_sensitivity=0.8,
            delegation=0.8,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            old_profile_path = Path(tmpdir) / "old-profile.json"
            new_profile_path = Path(tmpdir) / "new-profile.json"
            old_policy_path = Path(tmpdir) / "old-policy.json"
            report_path = Path(tmpdir) / "migration.json"
            old_profile_path.write_text(json.dumps(old_profile.to_dict()), encoding="utf-8")
            new_profile_path.write_text(json.dumps(new_profile.to_dict()), encoding="utf-8")

            with redirect_stdout(StringIO()):
                main(
                    [
                        "recommend",
                        "--profile",
                        str(old_profile_path),
                        "--out",
                        str(old_policy_path),
                    ]
                )

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "migrate",
                        "--from-profile",
                        str(old_profile_path),
                        "--to-profile",
                        str(new_profile_path),
                        "--from-policy",
                        str(old_policy_path),
                        "--out",
                        str(report_path),
                    ]
                )

            data = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(data, json.loads(report_path.read_text(encoding="utf-8")))
            self.assertTrue(data["policy_diff"])
            self.assertIn("module_diff", data)
            self.assertIn("harness_drift_score", data["metrics"])

    def test_refine_outputs_proposed_policy_from_trace(self) -> None:
        profile = ModelProfile(
            model_name="refine-model",
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
            run_path = Path(tmpdir) / "run.json"
            refine_path = Path(tmpdir) / "refine.json"
            profile_path.write_text(json.dumps(profile.to_dict()), encoding="utf-8")

            with redirect_stdout(StringIO()):
                main(["recommend", "--profile", str(profile_path), "--out", str(policy_path)])
                main(["assemble", "--policy", str(policy_path), "--out", str(spec_path)])
                main(
                    [
                        "run",
                        "--harness-spec",
                        str(spec_path),
                        "--task",
                        "tasks/eval",
                        "--provider",
                        "mock",
                        "--model",
                        "mock-model",
                        "--out",
                        str(run_path),
                    ]
                )

            trace_dir = Path(tmpdir) / "run-traces"
            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "refine",
                        "--policy",
                        str(policy_path),
                        "--trace",
                        str(trace_dir),
                        "--out",
                        str(refine_path),
                    ]
                )

            data = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(data, json.loads(refine_path.read_text(encoding="utf-8")))
            self.assertEqual(data["schema_version"], "0.8")
            self.assertIn("proposed_spec", data)

    def test_import_trace_normalizes_external_json(self) -> None:
        source = {
            "run_id": "external_cli",
            "task_id": "task_cli",
            "model_name": "external-model",
            "harness_name": "external-runtime",
            "events": [{"type": "llm_call", "total_tokens": 3}],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "external.json"
            out_path = Path(tmpdir) / "normalized.json"
            source_path.write_text(json.dumps(source), encoding="utf-8")

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "import-trace",
                        "--source",
                        str(source_path),
                        "--out",
                        str(out_path),
                    ]
                )

            data = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(data, json.loads(out_path.read_text(encoding="utf-8")))
            self.assertEqual(data["model_name"], "external-model")
            self.assertEqual(data["events"][0]["event_type"], "llm_call")

    def test_config_inspect_and_profile_use_project_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "adaharness.toml"
            profile_path = root / "profile.json"
            config_path.write_text(
                """
[providers.mock-provider]
type = "mock"

[models.mock-model]
provider = "mock-provider"

[defaults]
risk = "high"
budget = "constrained"
taskset = "tasks/profiler"
""",
                encoding="utf-8",
            )

            inspect_output = StringIO()
            with redirect_stdout(inspect_output):
                inspect_code = main(["config", "inspect", "--config", str(config_path)])

            validate_output = StringIO()
            with redirect_stdout(validate_output):
                validate_code = main(["config", "validate", "--config", str(config_path)])

            profile_output = StringIO()
            with redirect_stdout(profile_output):
                profile_code = main(
                    [
                        "profile",
                        "--config",
                        str(config_path),
                        "--model",
                        "mock-model",
                        "--out",
                        str(profile_path),
                    ]
                )

        self.assertEqual(inspect_code, 0)
        self.assertEqual(validate_code, 0)
        self.assertEqual(profile_code, 0)
        self.assertEqual(json.loads(validate_output.getvalue())["valid"], True)
        self.assertEqual(json.loads(profile_output.getvalue())["model_name"], "mock-model")
