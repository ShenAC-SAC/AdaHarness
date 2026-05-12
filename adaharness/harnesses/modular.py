from __future__ import annotations

from dataclasses import dataclass, replace

from adaharness.evals.task_schema import EvalTask
from adaharness.models.base import ModelClient, ModelUsage
from adaharness.modules.base import HarnessModule
from adaharness.modules.registry import ModuleRegistry
from adaharness.policies.schema import HarnessPolicy
from adaharness.runtime.budget import Budget
from adaharness.runtime.results import RunResult
from adaharness.runtime.tracing import RunTrace
from adaharness.specs import compile_policy_to_spec
from adaharness.specs.harness_spec import HarnessSpec


@dataclass(frozen=True)
class ModularHarness:
    name: str
    policy: HarnessPolicy
    spec: HarnessSpec
    modules: tuple[HarnessModule, ...]
    registry: ModuleRegistry

    def run(self, task: EvalTask, model: ModelClient, *, budget: Budget) -> RunResult:
        """Run with assembled modules by calling lifecycle hooks in order."""
        active_policy = self.policy
        active_modules = self.modules
        trace = RunTrace.start(
            task_id=task.id,
            model_name=model.model_name,
            harness_name=self.name,
            policy=active_policy,
        )
        trace = trace.add_event("task_start", category=task.category, difficulty=task.difficulty)
        for module in active_modules:
            trace = module.on_start(trace)

        attempt = 1
        while True:
            for module in active_modules:
                trace = module.before_model_call(trace, task, attempt=attempt, budget=budget)

            response = model.complete(
                [{"role": "user", "content": task.prompt}],
                temperature=0.0,
                max_tokens=min(1024, budget.max_tokens),
            )
            usage = response.usage or ModelUsage()
            trace = trace.add_event(
                "llm_call",
                attempt=attempt,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens,
            )
            for module in active_modules:
                trace = module.after_model_call(trace, task, response, attempt=attempt)

            verification_failed = any(module.verification_failed(response) for module in active_modules)
            retrying_modules = [
                module
                for module in active_modules
                if module.should_retry(verification_failed=verification_failed, attempt=attempt)
            ]
            if not retrying_modules:
                break

            active_policy, active_modules, trace = self._adapt_after_retry_signal(
                active_policy,
                active_modules,
                trace,
                verification_failed=verification_failed,
            )
            for module in active_modules:
                trace = module.on_retry(trace, attempt=attempt, reason="verification_failure")
            attempt += 1

        trace = trace.finish()
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

    def _adapt_after_retry_signal(
        self,
        policy: HarnessPolicy,
        modules: tuple[HarnessModule, ...],
        trace: RunTrace,
        *,
        verification_failed: bool,
    ) -> tuple[HarnessPolicy, tuple[HarnessModule, ...], RunTrace]:
        if not verification_failed:
            return policy, modules, trace

        updated_policy = replace(policy, verifier_strength="always", autonomy_budget="small")
        if updated_policy == policy:
            return policy, modules, trace

        updated_spec = compile_policy_to_spec(updated_policy, name=self.name)
        updated_modules = tuple(
            self.registry.create(module_spec)
            for module_spec in updated_spec.modules
            if module_spec.enabled
        )
        trace = trace.add_event(
            "policy_change",
            old_policy=policy.to_dict(),
            new_policy=updated_policy.to_dict(),
            reason="verification_failure",
        )
        trace = trace.add_event(
            "modules_rebuilt",
            enabled_modules=[module.name for module in updated_modules],
        )
        return updated_policy, updated_modules, trace
