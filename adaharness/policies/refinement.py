from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
import json

from adaharness.policies.migration import diff_policies
from adaharness.policies.schema import HarnessPolicy
from adaharness.runtime.tracing import RunTrace
from adaharness.specs import compile_policy_to_spec
from adaharness.specs.harness_spec import HarnessSpec


@dataclass(frozen=True)
class PolicyRefinement:
    current_policy: HarnessPolicy
    proposed_policy: HarnessPolicy
    proposed_spec: HarnessSpec
    policy_diff: tuple[dict[str, Any], ...]
    reasons: tuple[str, ...]
    trace_count: int
    schema_version: str = "0.8"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "current_policy": self.current_policy.to_dict(),
            "proposed_policy": self.proposed_policy.to_dict(),
            "proposed_spec": self.proposed_spec.to_dict(),
            "policy_diff": list(self.policy_diff),
            "reasons": list(self.reasons),
            "trace_count": self.trace_count,
        }


def load_traces(path: Path) -> tuple[RunTrace, ...]:
    if path.is_dir():
        return tuple(
            RunTrace.from_dict(json.loads(trace_path.read_text(encoding="utf-8")))
            for trace_path in sorted(path.glob("*.json"))
        )
    return (RunTrace.from_dict(json.loads(path.read_text(encoding="utf-8"))),)


def refine_policy_from_traces(
    policy: HarnessPolicy,
    traces: tuple[RunTrace, ...],
    *,
    name: str = "refined_harness",
) -> PolicyRefinement:
    proposed = policy
    reasons: list[str] = []
    if _has_failed_verification(traces):
        proposed = replace(proposed, verifier_strength="always")
        if proposed.retry_policy == "none":
            proposed = replace(proposed, retry_policy="bounded")
        reasons.append("Verification failures require stronger verification and retry coverage.")
    if _has_retries(traces) and proposed.autonomy_budget != "small":
        proposed = replace(proposed, autonomy_budget="small")
        reasons.append("Observed retries reduce the autonomy budget for the next run.")
    if _has_tool_activity(traces) and proposed.tool_gatekeeping == "none":
        proposed = replace(proposed, tool_gatekeeping="moderate")
        reasons.append("Tool activity without gatekeeping enables moderate tool checks.")
    if not reasons:
        reasons.append("No trace signal requires a policy change.")
    policy_diff = tuple(diff_policies(policy, proposed))
    return PolicyRefinement(
        current_policy=policy,
        proposed_policy=proposed,
        proposed_spec=compile_policy_to_spec(proposed, name=name),
        policy_diff=policy_diff,
        reasons=tuple(reasons),
        trace_count=len(traces),
    )


def _has_failed_verification(traces: tuple[RunTrace, ...]) -> bool:
    return any(
        event.event_type in {"verification", "verifier.check"} and event.payload.get("verdict") == "failed"
        for trace in traces
        for event in trace.events
    )


def _has_retries(traces: tuple[RunTrace, ...]) -> bool:
    return any(
        event.event_type in {"retry", "retry_controller.retry"}
        for trace in traces
        for event in trace.events
    )


def _has_tool_activity(traces: tuple[RunTrace, ...]) -> bool:
    return any(
        event.event_type in {"tool_executor.ready", "tool_gatekeeper.check"}
        for trace in traces
        for event in trace.events
    )
