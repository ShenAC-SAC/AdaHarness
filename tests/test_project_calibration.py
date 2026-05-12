import unittest

from adaharness import CalibrationResult
from adaharness.adapters import AdapterCapabilities
from adaharness.evals.task_schema import EvalTask
from adaharness.policies.presets import BARE_POLICY
from adaharness.project import ProjectRunResult, calibrate_project
from adaharness.runtime.tracing import RunTrace


class FakeProjectAdapter:
    name = "fake-agent-project"

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            supports_pre_model_hook=True,
            supports_post_model_hook=True,
            supports_tool_interception=True,
            supports_retry_loop=True,
            supports_trace_export=True,
        )

    def run_task(self, task: EvalTask, *, binding=None) -> ProjectRunResult:
        score = 0.8 if task.target_capability == "tool_use" else 0.4
        success = score >= task.difficulty
        trace = (
            RunTrace.start(
                task_id=task.id,
                model_name=self.name,
                harness_name="host-runtime",
                policy=BARE_POLICY,
            )
            .add_event("project.task", category=task.category, target=task.target_capability)
            .finish()
        )
        errors = () if success else (f"{task.id} failed in host runtime",)
        return ProjectRunResult(
            task_id=task.id,
            success=success,
            score=score,
            output="host output",
            trace=trace,
            errors=errors,
        )


class ProjectCalibrationTests(unittest.TestCase):
    def test_calibrate_project_outputs_policy_spec_and_binding(self) -> None:
        tasks = [
            EvalTask(
                id="tool",
                category="tool",
                prompt="Use a tool",
                difficulty=0.7,
                target_capability="tool_use",
            ),
            EvalTask(
                id="recovery",
                category="recovery",
                prompt="Recover from failure",
                difficulty=0.6,
                target_capability="recovery",
            ),
        ]

        result = calibrate_project(FakeProjectAdapter(), tasks)
        data = result.to_dict()

        self.assertIsInstance(result, CalibrationResult)
        self.assertEqual(result.profile.project_name, "fake-agent-project")
        self.assertEqual(result.profile.task_count, 2)
        self.assertEqual(result.profile.success_rate, 0.5)
        self.assertIn("recovery", result.profile.model_profile.weaknesses)
        self.assertEqual(result.recommendation.model_name, "fake-agent-project")
        self.assertEqual(result.spec.metadata["project"], "fake-agent-project")
        self.assertEqual(result.binding.runtime, "fake-agent-project")
        self.assertIn("planner", result.binding.bindings)
        self.assertIn("report", data)

    def test_calibrate_project_rejects_empty_taskset(self) -> None:
        with self.assertRaisesRegex(ValueError, "tasks must contain"):
            calibrate_project(FakeProjectAdapter(), [])
