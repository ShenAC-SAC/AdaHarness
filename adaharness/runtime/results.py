from __future__ import annotations

from dataclasses import dataclass, replace

from adaharness.models.base import ModelUsage
from adaharness.runtime.tracing import RunTrace


@dataclass(frozen=True)
class RunResult:
    task_id: str
    harness_name: str
    model_name: str
    success: bool
    score: float
    output: str
    trace: RunTrace
    usage: ModelUsage
    errors: tuple[str, ...] = ()
    estimated_cost: float = 1.0
    estimated_latency: float = 1.0

    def with_trace(self, trace: RunTrace) -> "RunResult":
        return replace(self, trace=trace)

    def with_outcome(
        self,
        *,
        success: bool,
        score: float,
        errors: tuple[str, ...] = (),
        estimated_cost: float,
        estimated_latency: float,
    ) -> "RunResult":
        trace = self.trace.add_event(
            "final",
            success=success,
            score=score,
            errors=list(errors),
            estimated_cost=estimated_cost,
            estimated_latency=estimated_latency,
        ).finish()
        return replace(
            self,
            success=success,
            score=score,
            errors=errors,
            estimated_cost=estimated_cost,
            estimated_latency=estimated_latency,
            trace=trace,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "harness_name": self.harness_name,
            "model_name": self.model_name,
            "success": self.success,
            "score": self.score,
            "output": self.output,
            "trace": self.trace.to_dict(),
            "usage": {
                "input_tokens": self.usage.input_tokens,
                "output_tokens": self.usage.output_tokens,
                "total_tokens": self.usage.total_tokens,
            },
            "errors": list(self.errors),
            "estimated_cost": self.estimated_cost,
            "estimated_latency": self.estimated_latency,
        }
