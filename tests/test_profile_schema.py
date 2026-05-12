import unittest

from adaharness.profiler.profile_schema import CapabilityScore, ModelProfile


class ProfileSchemaTests(unittest.TestCase):
    def test_legacy_flat_profile_loads(self) -> None:
        profile = ModelProfile.from_dict(
            {
                "model_name": "legacy",
                "planning": 0.6,
                "tool_use": 0.5,
                "instruction_following": 0.7,
                "self_verification": 0.4,
                "context_management": 0.6,
                "recovery": 0.5,
            }
        )

        self.assertEqual(profile.model_name, "legacy")
        self.assertEqual(profile.delegation, 0.5)
        self.assertIn("planning", profile.scores)

    def test_nested_score_profile_loads(self) -> None:
        profile = ModelProfile.from_dict(
            {
                "schema_version": "0.3",
                "model_name": "nested",
                "scores": {
                    "planning": {
                        "name": "planning",
                        "score": 0.71,
                        "confidence": 0.82,
                        "evidence": ["created dependency-aware plan"],
                    }
                },
                "tool_use": 0.5,
                "instruction_following": 0.7,
                "self_verification": 0.4,
                "context_management": 0.6,
                "recovery": 0.5,
            }
        )

        self.assertEqual(profile.planning, 0.71)
        self.assertEqual(profile.score_for("planning").confidence, 0.82)
        self.assertEqual(profile.to_dict()["schema_version"], "0.3")

    def test_nested_score_validates_unit_interval(self) -> None:
        with self.assertRaises(ValueError):
            CapabilityScore(name="planning", score=1.2, confidence=0.5)
