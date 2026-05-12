import unittest

from adaharness.adapters import AdapterCapabilities, GenericRuntimeAdapter, RuntimeBinding, bind_runtime
from adaharness.policies.presets import STRUCTURED_POLICY
from adaharness.specs import compile_policy_to_spec


class AdapterBindingTests(unittest.TestCase):
    def test_generic_adapter_reports_unsupported_controllers(self) -> None:
        spec = compile_policy_to_spec(STRUCTURED_POLICY, name="structured")

        binding = GenericRuntimeAdapter().bind(spec)

        self.assertIsInstance(binding, RuntimeBinding)
        self.assertIn("planner", binding.unsupported_controllers)
        self.assertIn("Controller planner requires supports_pre_model_hook.", binding.warnings)

    def test_generic_adapter_binds_supported_hooks(self) -> None:
        spec = compile_policy_to_spec(STRUCTURED_POLICY, name="structured")
        capabilities = AdapterCapabilities(
            supports_pre_model_hook=True,
            supports_post_model_hook=True,
            supports_tool_interception=True,
            supports_tool_execution=True,
            supports_retry_loop=True,
            supports_subagents=True,
            supports_trace_export=True,
        )

        binding = bind_runtime(spec, capabilities=capabilities, runtime="custom-python")

        self.assertEqual(binding.runtime, "custom-python")
        self.assertIn("planner", binding.bindings)
        self.assertEqual(binding.bindings["planner"]["hook"], "before_model_call")
        self.assertEqual(binding.bindings["planner"]["controller"], "planner")
        self.assertEqual(binding.bindings["planner"]["legacy_module"], "planner")
        self.assertIn("level", binding.bindings["planner"])
        self.assertEqual(binding.unsupported_controllers, ())
        self.assertEqual(binding.unsupported_modules, ())

    def test_binding_round_trips_from_dict(self) -> None:
        binding = RuntimeBinding(
            runtime="custom",
            spec_name="spec",
            enabled_features=("planner",),
            bindings={"planner": {"hook": "before_model_call"}},
            unsupported_controllers=("verifier",),
        )

        restored = RuntimeBinding.from_dict(binding.to_dict())

        self.assertEqual(restored, binding)
