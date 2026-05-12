from pathlib import Path
import unittest

from adaharness.profiler.runner import run_profiler


class ProfilerRunnerTests(unittest.TestCase):
    def test_default_profiler_remains_deterministic(self) -> None:
        profile = run_profiler("model")

        self.assertEqual(profile.model_name, "model")
        self.assertEqual(profile.planning, 0.62)

    def test_task_backed_profiler_returns_diagnostics(self) -> None:
        profile = run_profiler("model", taskset=Path("tasks/profiler"))

        self.assertIn("recovery", profile.weaknesses)
        self.assertIn("bounded_retry", profile.recommended_controls)
        self.assertTrue(profile.score_for("recovery").failed_cases)
