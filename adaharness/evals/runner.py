from __future__ import annotations

from adaharness.evals.metrics import HarnessMetrics, compute_relative_metrics
from adaharness.evals.task_schema import EvalTask
from adaharness.harnesses.base import Harness
from adaharness.profiler.profile_schema import ModelProfile


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


def compare_harnesses(
    profile: ModelProfile,
    harnesses: list[Harness],
    tasks: list[EvalTask],
) -> list[HarnessMetrics]:
    raw_metrics = [evaluate_harness(profile, harness, tasks) for harness in harnesses]
    return compute_relative_metrics(raw_metrics)
