import unittest

from adaharness.evals.task_schema import EvalTask
from adaharness.harnesses.builder import HarnessBuilder
from adaharness.models.mock import MockModelClient
from adaharness.modules.registry import ModuleRegistry
from adaharness.policies.presets import BARE_POLICY, STRUCTURED_POLICY
from adaharness.policies.presets import STRONG_POLICY
from adaharness.runtime.budget import Budget
from adaharness.specs import compile_policy_to_spec
from adaharness.specs.harness_spec import ModuleSpec


class ModuleBuilderTests(unittest.TestCase):
    def test_registry_creates_known_module(self) -> None:
        module = ModuleRegistry().create(ModuleSpec(name="planner", config={"depth": "explicit"}))

        self.assertEqual(module.name, "planner")
        self.assertEqual(module.config["depth"], "explicit")

    def test_registry_rejects_unknown_module(self) -> None:
        with self.assertRaises(ValueError):
            ModuleRegistry().create(ModuleSpec(name="unknown"))

    def test_builder_creates_modular_harness_from_spec(self) -> None:
        spec = compile_policy_to_spec(STRUCTURED_POLICY, name="structured_spec")

        harness = HarnessBuilder().build(spec)

        self.assertEqual(harness.name, "structured_spec")
        self.assertEqual(harness.policy, STRUCTURED_POLICY)
        self.assertIn("planner", [module.name for module in harness.modules])

    def test_builder_only_creates_enabled_modules(self) -> None:
        spec = compile_policy_to_spec(BARE_POLICY)

        harness = HarnessBuilder().build(spec)

        module_names = [module.name for module in harness.modules]
        self.assertIn("trace", module_names)
        self.assertNotIn("planner", module_names)

    def test_modular_runtime_records_policy_driven_behavior(self) -> None:
        task = EvalTask(
            id="tool_task",
            category="tool_use",
            prompt="Use a tool.",
            difficulty=0.5,
            target_capability="tool_use",
        )
        bare = HarnessBuilder().build(compile_policy_to_spec(BARE_POLICY, name="bare_spec"))
        strong = HarnessBuilder().build(compile_policy_to_spec(STRONG_POLICY, name="strong_spec"))

        bare_run = bare.run(task, MockModelClient(), budget=Budget())
        strong_run = strong.run(task, MockModelClient(), budget=Budget())

        bare_events = [event.event_type for event in bare_run.trace.events]
        strong_events = [event.event_type for event in strong_run.trace.events]
        self.assertNotIn("planner.plan", bare_events)
        self.assertIn("planner.plan", strong_events)
        self.assertIn("tool_gatekeeper.check", strong_events)
        self.assertIn("verifier.check", strong_events)

    def test_retry_controller_retries_after_verification_failure(self) -> None:
        task = EvalTask(
            id="recovery_task",
            category="recovery",
            prompt="Recover from a failed answer.",
            difficulty=0.5,
            target_capability="recovery",
        )
        harness = HarnessBuilder().build(compile_policy_to_spec(STRUCTURED_POLICY))
        model = MockModelClient(responses=("", "recovered response"))

        result = harness.run(task, model, budget=Budget())

        events = [event.event_type for event in result.trace.events]
        verifier_verdicts = [
            event.payload["verdict"]
            for event in result.trace.events
            if event.event_type == "verifier.check"
        ]
        self.assertEqual(verifier_verdicts, ["failed", "passed"])
        self.assertIn("retry_controller.retry", events)
        self.assertIn("recovery.recover", events)
