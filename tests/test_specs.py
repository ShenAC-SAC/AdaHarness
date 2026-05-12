import unittest

from adaharness.policies.presets import BARE_POLICY, STRONG_POLICY, STRUCTURED_POLICY
from adaharness.specs import HarnessSpec, compile_policy_to_spec


class HarnessSpecTests(unittest.TestCase):
    def test_compile_policy_includes_core_modules(self) -> None:
        spec = compile_policy_to_spec(BARE_POLICY)

        self.assertEqual(spec.schema_version, "0.4")
        self.assertIn("trace", spec.enabled_modules)
        self.assertIn("budget_guard", spec.enabled_modules)
        self.assertIn("tool_executor", spec.enabled_modules)
        self.assertIn("planner", spec.disabled_modules)
        self.assertIn("verifier", spec.disabled_modules)
        self.assertTrue(spec.requires("supports_trace_export"))

    def test_compile_structured_policy_enables_selected_modules(self) -> None:
        spec = compile_policy_to_spec(STRUCTURED_POLICY)

        self.assertIn("planner", spec.enabled_modules)
        self.assertIn("tool_gatekeeper", spec.enabled_modules)
        self.assertIn("verifier", spec.enabled_modules)
        self.assertIn("retry_controller", spec.enabled_modules)
        self.assertIn("context_manager", spec.enabled_modules)

    def test_strong_policy_compiles_module_config(self) -> None:
        spec = compile_policy_to_spec(STRONG_POLICY, name="strong_spec")
        data = spec.to_dict()
        planner = next(module for module in data["modules"] if module["name"] == "planner")
        verifier = next(module for module in data["modules"] if module["name"] == "verifier")

        self.assertEqual(data["name"], "strong_spec")
        self.assertEqual(data["source_policy"], STRONG_POLICY.to_dict())
        self.assertIn("requirements", data)
        self.assertIn("adapter_hints", data)
        self.assertEqual(planner["config"]["depth"], "strict")
        self.assertEqual(verifier["config"]["strength"], "always")

    def test_spec_round_trips_from_dict(self) -> None:
        spec = compile_policy_to_spec(STRUCTURED_POLICY)

        restored = HarnessSpec.from_dict(spec.to_dict())

        self.assertEqual(restored.to_dict(), spec.to_dict())

    def test_spec_loads_legacy_source_policy_from_metadata(self) -> None:
        data = compile_policy_to_spec(STRUCTURED_POLICY).to_dict()
        data["schema_version"] = "0.3"
        data["metadata"]["source_policy"] = STRUCTURED_POLICY.to_dict()
        data.pop("source_policy")
        data.pop("requirements")
        data.pop("adapter_hints")

        restored = HarnessSpec.from_dict(data)

        self.assertEqual(restored.source_policy, STRUCTURED_POLICY.to_dict())
