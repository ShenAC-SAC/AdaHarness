import unittest

from adaharness.policies.migration import build_migration_report, diff_policies
from adaharness.policies.presets import STRONG_POLICY
from adaharness.profiler.profile_schema import ModelProfile


class MigrationTests(unittest.TestCase):
    def test_diff_policies_reports_changed_fields(self) -> None:
        report = diff_policies(STRONG_POLICY, STRONG_POLICY)

        self.assertEqual(report, [])

    def test_migration_report_includes_policy_and_module_diffs(self) -> None:
        old_profile = ModelProfile(
            model_name="old-small",
            planning=0.35,
            tool_use=0.35,
            instruction_following=0.35,
            self_verification=0.35,
            context_management=0.35,
            recovery=0.35,
        )
        new_profile = ModelProfile(
            model_name="new-strong",
            planning=0.9,
            tool_use=0.9,
            instruction_following=0.9,
            self_verification=0.9,
            context_management=0.9,
            recovery=0.9,
            cost_sensitivity=0.8,
            delegation=0.8,
        )

        report = build_migration_report(
            from_profile=old_profile,
            to_profile=new_profile,
            from_policy=STRONG_POLICY,
        )
        data = report.to_dict()

        self.assertEqual(data["schema_version"], "0.7")
        self.assertEqual(data["from_model"], "old-small")
        self.assertEqual(data["to_model"], "new-strong")
        self.assertGreater(data["metrics"]["policy_delta"], 0)
        self.assertGreater(data["metrics"]["harness_drift_score"], 0)
        self.assertTrue(data["policy_diff"])
        self.assertTrue(data["module_diff"]["disabled"])
