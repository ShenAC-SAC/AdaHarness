import unittest

from adaharness.policies.generator import generate_policy
from adaharness.profiler.profile_schema import ModelProfile


class PolicyGeneratorTests(unittest.TestCase):
    def test_weak_profile_gets_strong_policy(self) -> None:
        profile = ModelProfile(
            model_name="weak",
            planning=0.2,
            tool_use=0.3,
            instruction_following=0.4,
            self_verification=0.2,
            context_management=0.3,
            recovery=0.2,
        )

        policy = generate_policy(profile)

        self.assertEqual(policy.planning_depth, "strict")
        self.assertEqual(policy.verifier_strength, "always")

    def test_strong_profile_gets_light_policy(self) -> None:
        profile = ModelProfile(
            model_name="strong",
            planning=0.9,
            tool_use=0.85,
            instruction_following=0.9,
            self_verification=0.8,
            context_management=0.82,
            recovery=0.86,
        )

        policy = generate_policy(profile)

        self.assertEqual(policy.planning_depth, "light")
        self.assertEqual(policy.retry_policy, "bounded")
