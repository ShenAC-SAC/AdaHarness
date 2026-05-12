from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adaharness.adapters.binding import RuntimeBinding
from adaharness.policies.artifacts import PolicyRecommendation
from adaharness.profiler.profile_schema import ModelProfile
from adaharness.project.adapter import ProjectRunResult
from adaharness.specs.harness_spec import HarnessSpec


@dataclass(frozen=True)
class AgentSystemProfile:
    """Project-level profile derived from host runtime calibration evidence."""

    project_name: str
    model_profile: ModelProfile
    task_count: int
    success_rate: float
    runtime_capabilities: dict[str, bool]
    failure_modes: tuple[str, ...] = ()
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not 0.0 <= self.success_rate <= 1.0:
            raise ValueError(f"success_rate must be between 0.0 and 1.0, got {self.success_rate!r}")
        object.__setattr__(self, "runtime_capabilities", dict(self.runtime_capabilities))
        object.__setattr__(self, "failure_modes", tuple(self.failure_modes))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_name": self.project_name,
            "model_profile": self.model_profile.to_dict(),
            "task_count": self.task_count,
            "success_rate": self.success_rate,
            "runtime_capabilities": self.runtime_capabilities,
            "failure_modes": list(self.failure_modes),
        }


@dataclass(frozen=True)
class CalibrationResult:
    """Artifacts produced by project-local calibration."""

    profile: AgentSystemProfile
    recommendation: PolicyRecommendation
    spec: HarnessSpec
    binding: RuntimeBinding
    runs: tuple[ProjectRunResult, ...]
    report: str
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "runs", tuple(self.runs))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "profile": self.profile.to_dict(),
            "recommendation": self.recommendation.to_dict(),
            "spec": self.spec.to_dict(),
            "binding": self.binding.to_dict(),
            "runs": [run.to_dict() for run in self.runs],
            "report": self.report,
        }
