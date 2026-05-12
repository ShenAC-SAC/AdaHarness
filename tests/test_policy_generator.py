import unittest

from adaharness.policies.generator import generate_policy
from adaharness.policies.generator import recommend_policy
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

    def test_high_risk_strengthens_controls(self) -> None:
        profile = ModelProfile(
            model_name="medium-risk",
            planning=0.65,
            tool_use=0.65,
            instruction_following=0.65,
            self_verification=0.65,
            context_management=0.65,
            recovery=0.65,
        )

        recommendation = recommend_policy(profile, risk="high", budget="standard")

        self.assertEqual(recommendation.risk, "high")
        self.assertEqual(recommendation.policy.planning_depth, "strict")
        self.assertEqual(recommendation.policy.tool_gatekeeping, "strict")
        self.assertEqual(recommendation.policy.verifier_strength, "always")
        self.assertIn("High risk", recommendation.rationale[1])

    def test_constrained_budget_reduces_expensive_controls(self) -> None:
        profile = ModelProfile(
            model_name="budget",
            planning=0.65,
            tool_use=0.65,
            instruction_following=0.65,
            self_verification=0.65,
            context_management=0.65,
            recovery=0.65,
        )

        recommendation = recommend_policy(profile, risk="medium", budget="constrained")

        self.assertEqual(recommendation.budget, "constrained")
        self.assertEqual(recommendation.policy.planning_depth, "light")
        self.assertEqual(recommendation.policy.retry_policy, "none")
        self.assertEqual(recommendation.policy.context_policy, "summarized")
