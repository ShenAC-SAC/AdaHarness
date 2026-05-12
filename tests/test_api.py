from pathlib import Path
import tempfile
import unittest

from adaharness import (
    bind_harness_spec,
    build_reference_harness,
    compile_harness_spec,
    load_policy,
    load_policy_recommendation,
    load_profile,
    load_project_config,
    load_spec,
    profile_model,
    recommend_harness_policy,
    save_artifact,
)
from adaharness.adapters import AdapterCapabilities
from adaharness.policies.artifacts import PolicyRecommendation
from adaharness.specs.harness_spec import HarnessSpec


class PublicApiTests(unittest.TestCase):
    def test_embedded_policy_workflow(self) -> None:
        profile = profile_model("api-model", taskset=Path("tasks/profiler"))

        recommendation = recommend_harness_policy(profile, risk="medium", budget="standard")
        spec = compile_harness_spec(recommendation, name="api-spec")
        harness = build_reference_harness(spec)

        self.assertIsInstance(recommendation, PolicyRecommendation)
        self.assertIsInstance(spec, HarnessSpec)
        self.assertEqual(harness.name, "api-spec")
        self.assertEqual(spec.metadata["recommendation"]["model_name"], "api-model")

    def test_public_api_binds_spec_to_runtime_capabilities(self) -> None:
        profile = profile_model("binding-api")
        recommendation = recommend_harness_policy(profile)
        spec = compile_harness_spec(recommendation)

        binding = bind_harness_spec(
            spec,
            runtime="custom-python",
            capabilities=AdapterCapabilities(
                supports_pre_model_hook=True,
                supports_post_model_hook=True,
                supports_tool_interception=True,
                supports_tool_execution=True,
                supports_retry_loop=True,
                supports_subagents=True,
                supports_trace_export=True,
            ),
        )

        self.assertEqual(binding.runtime, "custom-python")
        self.assertIn("planner", binding.bindings)

    def test_artifact_load_save_helpers(self) -> None:
        profile = profile_model("artifact-api")
        recommendation = recommend_harness_policy(profile)
        spec = compile_harness_spec(recommendation)

        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            policy_path = Path(tmpdir) / "policy.json"
            spec_path = Path(tmpdir) / "spec.json"
            save_artifact(profile_path, profile)
            save_artifact(policy_path, recommendation)
            save_artifact(spec_path, spec)

            self.assertEqual(load_profile(profile_path).model_name, "artifact-api")
            self.assertEqual(load_policy(policy_path), recommendation.policy)
            self.assertEqual(load_policy_recommendation(policy_path), recommendation)
            self.assertEqual(load_spec(spec_path).to_dict(), spec.to_dict())

    def test_public_api_loads_project_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "adaharness.toml"
            config_path.write_text(
                """
[providers.mock-provider]
type = "mock"

[models.mock-model]
provider = "mock-provider"
""",
                encoding="utf-8",
            )

            config = load_project_config(config_path)

        self.assertEqual(config.resolve_model("mock-model").provider, "mock")
