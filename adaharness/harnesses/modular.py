from __future__ import annotations

from dataclasses import dataclass

from adaharness.evals.task_schema import EvalTask
from adaharness.models.base import ModelClient, ModelUsage
from adaharness.modules.base import HarnessModule
from adaharness.policies.schema import HarnessPolicy
from adaharness.runtime.budget import Budget
from adaharness.runtime.results import RunResult
from adaharness.runtime.tracing import RunTrace
from adaharness.specs.harness_spec import HarnessSpec


@dataclass(frozen=True)
class ModularHarness:
    name: str
    policy: HarnessPolicy
    spec: HarnessSpec
    modules: tuple[HarnessModule, ...]

    def run(self, task: EvalTask, model: ModelClient, *, budget: Budget) -> RunResult:
        """Run with assembled modules; v0.4 modules only record activation."""
        trace = RunTrace.start(
            task_id=task.id,
            model_name=model.model_name,
            harness_name=self.name,
            policy=self.policy,
        )
        trace = trace.add_event("task_start", category=task.category, difficulty=task.difficulty)
        for module in self.modules:
            trace = module.on_start(trace)

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
        ).finish()
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
