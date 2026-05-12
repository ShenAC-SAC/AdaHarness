from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from adaharness.adapters import AdapterCapabilities
from adaharness.adapters.binding import RuntimeBinding
from adaharness.evals.task_schema import EvalTask
from adaharness.runtime.tracing import RunTrace


@dataclass(frozen=True)
class ProjectRunResult:
    """Result returned by a host agent project for one calibration task."""

    task_id: str
    success: bool
    score: float
    output: str
    trace: RunTrace
    errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be between 0.0 and 1.0, got {self.score!r}")
        object.__setattr__(self, "errors", tuple(self.errors))

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "score": self.score,
            "output": self.output,
            "trace": self.trace.to_dict(),
            "errors": list(self.errors),
        }


class ProjectAgentAdapter(Protocol):
    """Host-project adapter used by AdaHarness calibration."""

    name: str

    def capabilities(self) -> AdapterCapabilities:
        ...

    def run_task(
        self,
        task: EvalTask,
        *,
        binding: RuntimeBinding | None = None,
    ) -> ProjectRunResult:
        ...
