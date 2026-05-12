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

    def test_profile_accepts_provider_options(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(["profile", "--provider", "mock", "--model", "mock-model"])

        data = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(data["model_name"], "mock-model")
