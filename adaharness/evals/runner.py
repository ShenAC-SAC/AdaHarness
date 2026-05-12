from __future__ import annotations

from adaharness.evals.metrics import HarnessMetrics, compute_relative_metrics
from adaharness.evals.task_schema import EvalTask
from adaharness.harnesses.base import Harness
from adaharness.harnesses.runtime import runtime_for_harness
from adaharness.models.base import ModelClient
from adaharness.models.mock import MockModelClient
from adaharness.profiler.profile_schema import ModelProfile
from adaharness.runtime.budget import Budget
from adaharness.runtime.results import RunResult


def estimate_task_success(profile: ModelProfile, harness: Harness, task: EvalTask) -> bool:
    capability = getattr(profile, task.target_capability)
    support = harness.complexity_weight * (1.0 - capability) * 0.85
    tax = max(0.0, capability - 0.78) * harness.complexity_weight * 0.35
    effective_capability = min(1.0, capability + support - tax)
    return effective_capability >= task.difficulty


def evaluate_harness(
    profile: ModelProfile,
    harness: Harness,
    tasks: list[EvalTask],
) -> HarnessMetrics:
    if not tasks:
        raise ValueError("taskset must contain at least one task")

    successes = sum(1 for task in tasks if estimate_task_success(profile, harness, task))
    success_rate = successes / len(tasks)
    complexity = harness.complexity_weight
    estimated_cost = 1.0 + complexity * 0.7
    estimated_latency = 1.0 + complexity * 0.9
    retry_count = round(complexity * len(tasks))

    return HarnessMetrics(
        harness_name=harness.name,
        success_rate=success_rate,
        estimated_cost=estimated_cost,
        estimated_latency=estimated_latency,
        retry_count=retry_count,
    )


def run_harness(
    profile: ModelProfile,
    harness: Harness,
    tasks: list[EvalTask],
    *,
    model: ModelClient | None = None,
    budget: Budget | None = None,
) -> list[RunResult]:
    if not tasks:
        raise ValueError("taskset must contain at least one task")

    runtime = runtime_for_harness(harness)
    model_client = model or MockModelClient(model_name=profile.model_name)
    run_budget = budget or Budget()
    results = []
    for task in tasks:
        raw_result = runtime.run(task, model_client, policy=harness.policy, budget=run_budget)
        success = estimate_task_success(profile, harness, task)
        errors = () if success else (f"{task.id} did not meet {task.target_capability} difficulty",)
        trace = raw_result.trace
        if harness.policy.verifier_strength != "none":
            trace = trace.add_event(
                "verification",
                strength=harness.policy.verifier_strength,
                verdict="passed" if success else "failed",
            )
        if not success and harness.policy.retry_policy != "none":
            retry_limit = 1 if harness.policy.retry_policy == "bounded" else run_budget.max_retries
            for attempt in range(1, retry_limit + 1):
                trace = trace.add_event("retry", policy=harness.policy.retry_policy, attempt=attempt)
        raw_result = raw_result.with_trace(trace)
        complexity = harness.complexity_weight
        results.append(
            raw_result.with_outcome(
                success=success,
                score=1.0 if success else 0.0,
                errors=errors,
                estimated_cost=1.0 + complexity * 0.7,
                estimated_latency=1.0 + complexity * 0.9,
            )
        )
    return results


def evaluate_harness_runs(results: list[RunResult]) -> HarnessMetrics:
    if not results:
        raise ValueError("results must contain at least one run")

    success_rate = sum(1 for result in results if result.success) / len(results)
    estimated_cost = sum(result.estimated_cost for result in results) / len(results)
    estimated_latency = sum(result.estimated_latency for result in results) / len(results)
    retry_count = sum(
        1
        for result in results
        for event in result.trace.events
        if event.event_type == "retry"
    )
    return HarnessMetrics(
        harness_name=results[0].harness_name,
        success_rate=success_rate,
        estimated_cost=estimated_cost,
        estimated_latency=estimated_latency,
        retry_count=retry_count,
    )


def compare_harness_runs(
    profile: ModelProfile,
    harnesses: list[Harness],
    tasks: list[EvalTask],
    *,
    model: ModelClient | None = None,
    budget: Budget | None = None,
    baseline_name: str = "bare",
) -> tuple[list[HarnessMetrics], list[RunResult]]:
    runs = [
        result
        for harness in harnesses
        for result in run_harness(profile, harness, tasks, model=model, budget=budget)
    ]
    raw_metrics = [
        evaluate_harness_runs([result for result in runs if result.harness_name == harness.name])
        for harness in harnesses
    ]
    return compute_relative_metrics(raw_metrics, baseline_name=baseline_name), runs


def compare_harnesses(
    profile: ModelProfile,
    harnesses: list[Harness],
    tasks: list[EvalTask],
) -> list[HarnessMetrics]:
    raw_metrics = [evaluate_harness(profile, harness, tasks) for harness in harnesses]
    return compute_relative_metrics(raw_metrics)
