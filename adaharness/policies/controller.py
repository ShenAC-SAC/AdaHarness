from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from adaharness.policies.schema import HarnessPolicy
from adaharness.runtime.tracing import TraceEvent


class PolicyController(Protocol):
    def observe(self, event: TraceEvent, policy: HarnessPolicy) -> None:
        ...

    def maybe_update_policy(self) -> HarnessPolicy | None:
        ...


@dataclass
class TracePolicyController:
    current_policy: HarnessPolicy
    _pending_policy: HarnessPolicy | None = None
    _reason: str = ""

    @property
    def reason(self) -> str:
        return self._reason

    def observe(self, event: TraceEvent, policy: HarnessPolicy) -> None:
        self.current_policy = policy
        if event.event_type == "verification" and event.payload.get("verdict") == "failed":
            self._pending_policy = replace(policy, verifier_strength="always")
            self._reason = "verification failed"
            return
        if event.event_type == "retry":
            self._pending_policy = replace(policy, autonomy_budget="small")
            self._reason = "retry emitted"
            return
        if event.event_type == "llm_call":
            max_tokens = event.payload.get("max_tokens")
            total_tokens = event.payload.get("total_tokens")
            if isinstance(max_tokens, int) and isinstance(total_tokens, int) and total_tokens > max_tokens * 0.8:
                self._pending_policy = replace(policy, planning_depth=_loosen_planning(policy.planning_depth))
                self._reason = "token budget pressure"

    def maybe_update_policy(self) -> HarnessPolicy | None:
        policy = self._pending_policy
        self._pending_policy = None
        return policy


def _loosen_planning(planning_depth: str) -> str:
    order = ["none", "light", "explicit", "strict"]
    index = order.index(planning_depth)
    return order[max(0, index - 1)]
