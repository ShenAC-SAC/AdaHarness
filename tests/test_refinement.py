from pathlib import Path
import json
import tempfile
import unittest

from adaharness.evals.task_schema import EvalTask
from adaharness.harnesses.builder import HarnessBuilder
from adaharness.models.mock import MockModelClient
from adaharness.policies.presets import STRUCTURED_POLICY
from adaharness.policies.refinement import load_traces, refine_policy_from_traces
from adaharness.runtime.budget import Budget
from adaharness.runtime.tracing import RunTrace
from adaharness.specs import compile_policy_to_spec


class PolicyRefinementTests(unittest.TestCase):
    def test_run_trace_round_trips_from_dict(self) -> None:
        harness = HarnessBuilder().build(compile_policy_to_spec(STRUCTURED_POLICY))
        task = EvalTask(
            id="trace_task",
            category="recovery",
            prompt="Return an answer.",
            difficulty=0.5,
            target_capability="recovery",
        )

        result = harness.run(task, MockModelClient(), budget=Budget())

        restored = RunTrace.from_dict(result.trace.to_dict())
        self.assertEqual(restored.to_dict(), result.trace.to_dict())

    def test_refine_strengthens_policy_after_failed_verification(self) -> None:
        harness = HarnessBuilder().build(compile_policy_to_spec(STRUCTURED_POLICY))
        task = EvalTask(
            id="failed_trace",
            category="recovery",
            prompt="Recover.",
            difficulty=0.5,
            target_capability="recovery",
        )
        result = harness.run(task, MockModelClient(responses=("", "fixed")), budget=Budget())

        refinement = refine_policy_from_traces(STRUCTURED_POLICY, (result.trace,))
        data = refinement.to_dict()

        self.assertEqual(data["schema_version"], "0.8")
        self.assertEqual(data["proposed_policy"]["verifier_strength"], "always")
        self.assertEqual(data["proposed_policy"]["autonomy_budget"], "small")
        self.assertTrue(data["policy_diff"])

    def test_load_traces_reads_directory(self) -> None:
        harness = HarnessBuilder().build(compile_policy_to_spec(STRUCTURED_POLICY))
        task = EvalTask(
            id="load_trace",
            category="planning",
            prompt="Plan.",
            difficulty=0.5,
            target_capability="planning",
        )
        result = harness.run(task, MockModelClient(), budget=Budget())
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = Path(tmpdir) / "trace.json"
            trace_path.write_text(json.dumps(result.trace.to_dict()), encoding="utf-8")

            traces = load_traces(Path(tmpdir))

        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0].run_id, result.trace.run_id)
