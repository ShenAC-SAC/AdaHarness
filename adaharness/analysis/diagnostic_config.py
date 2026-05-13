from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10 in CI.
    import tomli as tomllib


@dataclass(frozen=True)
class VerifierOverconstraintConfig:
    min_events: int = 5
    max_catch_rate: float = 0.05
    min_cost_share: float = 0.20


@dataclass(frozen=True)
class PlannerOverconstraintConfig:
    min_events: int = 5
    min_latency_share: float = 0.25
    min_success_rate: float = 0.80


@dataclass(frozen=True)
class RetryOverconstraintConfig:
    min_events: int = 5
    max_success_rate: float = 0.20


@dataclass(frozen=True)
class ToolFailureConfig:
    min_tool_calls: int = 1
    min_failure_rate: float = 0.15


@dataclass(frozen=True)
class ToolIgnoredConfig:
    min_tool_calls: int = 1
    min_ignored_rate: float = 0.05


@dataclass(frozen=True)
class MissingVerifierConfig:
    min_final_events: int = 1
    min_failure_rate: float = 0.15


@dataclass(frozen=True)
class MissingRetryConfig:
    min_final_events: int = 1
    min_failure_rate: float = 0.15
    min_failed_without_retry_rate: float = 0.50


@dataclass(frozen=True)
class ConfidenceConfig:
    medium_evidence_count: int = 20
    high_evidence_count: int = 100


@dataclass(frozen=True)
class DiagnosticConfig:
    verifier_overconstraint: VerifierOverconstraintConfig = field(
        default_factory=VerifierOverconstraintConfig
    )
    planner_overconstraint: PlannerOverconstraintConfig = field(
        default_factory=PlannerOverconstraintConfig
    )
    retry_overconstraint: RetryOverconstraintConfig = field(default_factory=RetryOverconstraintConfig)
    tool_failure: ToolFailureConfig = field(default_factory=ToolFailureConfig)
    tool_result_ignored: ToolIgnoredConfig = field(default_factory=ToolIgnoredConfig)
    missing_verifier: MissingVerifierConfig = field(default_factory=MissingVerifierConfig)
    missing_retry: MissingRetryConfig = field(default_factory=MissingRetryConfig)
    confidence: ConfidenceConfig = field(default_factory=ConfidenceConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiagnosticConfig":
        diagnostics = data.get("diagnostics", data)
        return cls(
            verifier_overconstraint=VerifierOverconstraintConfig(
                **diagnostics.get("verifier_overconstraint", {})
            ),
            planner_overconstraint=PlannerOverconstraintConfig(
                **diagnostics.get("planner_overconstraint", {})
            ),
            retry_overconstraint=RetryOverconstraintConfig(
                **diagnostics.get("retry_overconstraint", {})
            ),
            tool_failure=ToolFailureConfig(**diagnostics.get("tool_failure", {})),
            tool_result_ignored=ToolIgnoredConfig(**diagnostics.get("tool_result_ignored", {})),
            missing_verifier=MissingVerifierConfig(**diagnostics.get("missing_verifier", {})),
            missing_retry=MissingRetryConfig(**diagnostics.get("missing_retry", {})),
            confidence=ConfidenceConfig(**diagnostics.get("confidence", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_diagnostic_config(path: str | Path | None = None) -> DiagnosticConfig:
    if path is None:
        return DiagnosticConfig()
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return DiagnosticConfig.from_dict(data)
