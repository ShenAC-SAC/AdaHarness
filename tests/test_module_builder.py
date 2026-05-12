import unittest

from adaharness.harnesses.builder import HarnessBuilder
from adaharness.modules.registry import ModuleRegistry
from adaharness.policies.presets import BARE_POLICY, STRUCTURED_POLICY
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
