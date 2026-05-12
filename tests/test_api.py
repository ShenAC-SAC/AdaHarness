from pathlib import Path
import tempfile
import unittest

from adaharness import (
    build_reference_harness,
    compile_harness_spec,
    load_policy,
    load_policy_recommendation,
    load_profile,
    load_spec,
    profile_model,
    recommend_harness_policy,
    save_artifact,
)
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
