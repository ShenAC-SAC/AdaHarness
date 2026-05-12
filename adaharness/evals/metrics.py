from __future__ import annotations

from dataclasses import asdict, dataclass, replace


@dataclass(frozen=True)
class HarnessMetrics:
    harness_name: str
    success_rate: float
    estimated_cost: float
    estimated_latency: float
    retry_count: int
    harness_lift: float = 0.0
    harness_tax: float = 1.0
    minimal_effective_harness_score: float = 0.0
    overconstraint_penalty: float = 0.0
    adaptation_gain: float = 0.0

    def to_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


def compute_relative_metrics(
    metrics: list[HarnessMetrics],
    baseline_name: str = "bare",
) -> list[HarnessMetrics]:
    baseline = next(item for item in metrics if item.harness_name == baseline_name)
    normalized = []
    for item in metrics:
        harness_lift = item.success_rate - baseline.success_rate
        harness_tax = item.estimated_cost / baseline.estimated_cost if baseline.estimated_cost else 1.0
        latency_ratio = (
            item.estimated_latency / baseline.estimated_latency
            if baseline.estimated_latency
            else 1.0
        )
        cost_penalty = max(0.0, harness_tax - 1.0) * 0.15
        latency_penalty = max(0.0, latency_ratio - 1.0) * 0.05
        score = item.success_rate - cost_penalty - latency_penalty
        overconstraint_penalty = max(0.0, cost_penalty + latency_penalty - max(0.0, harness_lift))
        normalized.append(
            HarnessMetrics(
                harness_name=item.harness_name,
                success_rate=item.success_rate,
                estimated_cost=item.estimated_cost,
                estimated_latency=item.estimated_latency,
                retry_count=item.retry_count,
                harness_lift=harness_lift,
                harness_tax=harness_tax,
                minimal_effective_harness_score=score,
                overconstraint_penalty=overconstraint_penalty,
            )
        )
    fixed_best = max(
        (
            item.minimal_effective_harness_score
            for item in normalized
            if item.harness_name != "adaptive"
        ),
        default=0.0,
    )
    return [
        replace(
            item,
            adaptation_gain=(
                item.minimal_effective_harness_score - fixed_best
                if item.harness_name == "adaptive"
                else 0.0
            ),
        )
        for item in normalized
    ]
