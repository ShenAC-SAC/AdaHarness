from pathlib import Path
import unittest

from adaharness.evals.runner import compare_harness_runs, run_harness
from adaharness.evals.task_schema import load_taskset
from adaharness.harnesses import BARE_HARNESS, LIGHT_HARNESS
from adaharness.profiler.runner import run_profiler


class HarnessRuntimeTests(unittest.TestCase):
    def test_run_harness_records_trace_events(self) -> None:
        profile = run_profiler("mock")
        task = load_taskset(Path("tasks/eval"))[0]

        result = run_harness(profile, BARE_HARNESS, [task])[0]

        event_types = [event.event_type for event in result.trace.events]
        self.assertIn("task_start", event_types)
        self.assertIn("llm_call", event_types)
        self.assertIn("final", event_types)

    def test_compare_harness_runs_returns_metrics_and_runs(self) -> None:
        profile = run_profiler("mock")
        tasks = load_taskset(Path("tasks/eval"))

        metrics, runs = compare_harness_runs(profile, [BARE_HARNESS, LIGHT_HARNESS], tasks)

        self.assertEqual(len(metrics), 2)
        self.assertEqual(len(runs), len(tasks) * 2)
        self.assertEqual(metrics[0].harness_name, "bare")

    def test_failed_bounded_policy_records_retry(self) -> None:
        profile = run_profiler("mock")
        tasks = load_taskset(Path("tasks/eval"))

        metrics, runs = compare_harness_runs(profile, [LIGHT_HARNESS], tasks, baseline_name="light")

        event_types = [
            event.event_type
            for run in runs
            if run.task_id == "recovery_001"
            for event in run.trace.events
        ]
        self.assertIn("retry", event_types)
        self.assertEqual(metrics[0].retry_count, 1)
