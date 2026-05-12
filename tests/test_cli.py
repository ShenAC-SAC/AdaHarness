from adaharness.cli import main
from contextlib import redirect_stdout
from io import StringIO
import json
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
                    "bare,adaptive",
                    "--taskset",
                    "tasks/eval",
                ]
            )

        data = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(data["comparisons"]), 2)
        self.assertEqual(len(data["comparisons"][0]["results"]), 2)

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
