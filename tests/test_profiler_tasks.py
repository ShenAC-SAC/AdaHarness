from pathlib import Path
import unittest

from adaharness.profiler.tasks import ProfilerTask, load_profiler_taskset


class ProfilerTaskTests(unittest.TestCase):
    def test_load_profiler_taskset(self) -> None:
        tasks = load_profiler_taskset(Path("tasks/profiler"))

        capabilities = {task.capability for task in tasks}

        self.assertIn("planning", capabilities)
        self.assertIn("delegation", capabilities)
        self.assertTrue(all(task.rubric.success_criteria for task in tasks))

    def test_unknown_capability_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ProfilerTask(
                id="bad",
                capability="unknown",
                prompt="bad",
                difficulty=0.5,
            )
