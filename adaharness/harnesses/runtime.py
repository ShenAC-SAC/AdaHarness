from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from adaharness.evals.task_schema import EvalTask
from adaharness.harnesses.base import Harness
from adaharness.models.base import ModelClient, ModelUsage
from adaharness.policies.schema import HarnessPolicy
from adaharness.runtime.budget import Budget
from adaharness.runtime.results import RunResult
from adaharness.runtime.tracing import RunTrace


class HarnessRuntime(Protocol):
    name: str

    def run(
        self,
        task: EvalTask,
        model: ModelClient,
        *,
        policy: HarnessPolicy,
        budget: Budget,
    ) -> RunResult:
        ...


@dataclass(frozen=True)
class PolicyHarnessRuntime:
    name: str

    def run(
        self,
        task: EvalTask,
        model: ModelClient,
        *,
        policy: HarnessPolicy,
        budget: Budget,
    ) -> RunResult:
        trace = RunTrace.start(
            task_id=task.id,
            model_name=model.model_name,
            harness_name=self.name,
            policy=policy,
        )
        trace = trace.add_event("task_start", category=task.category, difficulty=task.difficulty)
        trace = self._record_policy_controls(trace, policy)
        response = model.complete(
            [{"role": "user", "content": task.prompt}],
            temperature=0.0,
            max_tokens=min(1024, budget.max_tokens),
        )
        usage = response.usage or ModelUsage()
        trace = trace.add_event(
            "llm_call",
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
        )
        if policy.verifier_strength != "none":
            trace = trace.add_event("verification", strength=policy.verifier_strength, verdict="pending")

        return RunResult(
            task_id=task.id,
            harness_name=self.name,
            model_name=model.model_name,
            success=False,
            score=0.0,
            output=response.text,
            trace=trace,
            usage=usage,
        )

    def _record_policy_controls(self, trace: RunTrace, policy: HarnessPolicy) -> RunTrace:
        if policy.planning_depth != "none":
            trace = trace.add_event("planning", depth=policy.planning_depth)
        if policy.tool_gatekeeping != "none":
            trace = trace.add_event("tool_gatekeeping", strength=policy.tool_gatekeeping)
        if policy.context_policy != "raw":
            trace = trace.add_event("context_management", policy=policy.context_policy)
        if policy.subagent_policy not in {"disabled", "optional"}:
            trace = trace.add_event("delegation", policy=policy.subagent_policy)
        return trace


class BareRuntime(PolicyHarnessRuntime):
    def __init__(self) -> None:
        super().__init__("bare")


class LightRuntime(PolicyHarnessRuntime):
    def __init__(self) -> None:
        super().__init__("light")


class StructuredRuntime(PolicyHarnessRuntime):
    def __init__(self) -> None:
        super().__init__("structured")


class StrongRuntime(PolicyHarnessRuntime):
    def __init__(self) -> None:
        super().__init__("strong")


class AdaptiveRuntime(PolicyHarnessRuntime):
    def __init__(self) -> None:
        super().__init__("adaptive")


def runtime_for_harness(harness: Harness) -> HarnessRuntime:
    runtimes: dict[str, HarnessRuntime] = {
        "bare": BareRuntime(),
        "light": LightRuntime(),
        "structured": StructuredRuntime(),
        "strong": StrongRuntime(),
        "adaptive": AdaptiveRuntime(),
    }
    return runtimes.get(harness.name, PolicyHarnessRuntime(harness.name))
