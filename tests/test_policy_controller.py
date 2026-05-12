from pathlib import Path
import unittest

from adaharness.evals.runner import compare_harness_runs
from adaharness.evals.task_schema import load_taskset
from adaharness.harnesses import build_adaptive_harness
from adaharness.policies.controller import TracePolicyController
from adaharness.policies.presets import STRUCTURED_POLICY
from adaharness.profiler.runner import run_profiler
from adaharness.runtime.tracing import TraceEvent


class PolicyControllerTests(unittest.TestCase):
    def test_verification_failure_tightens_verifier(self) -> None:
        controller = TracePolicyController(STRUCTURED_POLICY)
        controller.observe(
            TraceEvent.create("verification", {"verdict": "failed"}),
            STRUCTURED_POLICY,
        )

        updated = controller.maybe_update_policy()

        self.assertIsNotNone(updated)
        self.assertEqual(updated.verifier_strength, "always")

    def test_adaptive_run_records_policy_change(self) -> None:
        profile = run_profiler("medium-sim")
        harness = build_adaptive_harness(profile)
        tasks = load_taskset(Path("tasks/eval"))

        _, runs = compare_harness_runs(profile, [harness], tasks, baseline_name="adaptive")

        event_types = [event.event_type for run in runs for event in run.trace.events]
        self.assertIn("policy_change", event_types)
