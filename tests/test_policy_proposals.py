from pathlib import Path
import unittest

from adaharness.evals.task_schema import load_taskset
from adaharness.policies.proposals import compare_policy_proposal, load_policy_proposal
from adaharness.profiler.runner import run_profiler


class PolicyProposalTests(unittest.TestCase):
    def test_load_policy_proposal(self) -> None:
        proposal = load_policy_proposal(Path("examples/policy_proposal.json"))

        self.assertEqual(proposal.policy.planning_depth, "strict")
        self.assertIn("weak recovery", proposal.rationale)

    def test_compare_policy_proposal_against_rule_policy(self) -> None:
        profile = run_profiler("small-sim")
        proposal = load_policy_proposal(Path("examples/policy_proposal.json"))
        tasks = load_taskset(Path("tasks/eval"))

        comparison = compare_policy_proposal(profile, proposal, tasks)

        self.assertEqual(comparison["results"][0]["harness_name"], "rule")
        self.assertEqual(comparison["results"][1]["harness_name"], "proposal")
