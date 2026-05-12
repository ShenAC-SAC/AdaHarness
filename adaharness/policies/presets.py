from __future__ import annotations

from adaharness.policies.schema import HarnessPolicy


BARE_POLICY = HarnessPolicy(
    planning_depth="none",
    tool_gatekeeping="none",
    verifier_strength="none",
    retry_policy="none",
    autonomy_budget="large",
    subagent_policy="disabled",
    context_policy="raw",
)

LIGHT_POLICY = HarnessPolicy(
    planning_depth="light",
    tool_gatekeeping="moderate",
    verifier_strength="selective",
    retry_policy="bounded",
    autonomy_budget="large",
    subagent_policy="optional",
    context_policy="raw",
)

STRUCTURED_POLICY = HarnessPolicy(
    planning_depth="explicit",
    tool_gatekeeping="moderate",
    verifier_strength="selective",
    retry_policy="bounded",
    autonomy_budget="medium",
    subagent_policy="optional",
    context_policy="retrieval_augmented",
)

STRONG_POLICY = HarnessPolicy(
    planning_depth="strict",
    tool_gatekeeping="strict",
    verifier_strength="always",
    retry_policy="aggressive",
    autonomy_budget="small",
    subagent_policy="recommended",
    context_policy="summarized",
)

PRESETS = {
    "bare": BARE_POLICY,
    "light": LIGHT_POLICY,
    "structured": STRUCTURED_POLICY,
    "strong": STRONG_POLICY,
}
