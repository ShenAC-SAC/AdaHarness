from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json

from adaharness.policies.schema import (
    BUDGET_LEVELS,
    RISK_LEVELS,
    BudgetLevel,
    HarnessPolicy,
    RiskLevel,
)


@dataclass(frozen=True)
class PolicyRecommendation:
    """Reusable recommendation artifact written by `adaharness recommend`."""

    model_name: str
    capability_average: float
    risk: RiskLevel
    budget: BudgetLevel
    policy: HarnessPolicy
    rationale: tuple[str, ...] = ()
    source: str = "rule_based"
    profile_schema_version: str = "unknown"
    schema_version: str = "0.2"

    def __post_init__(self) -> None:
        if self.risk not in RISK_LEVELS:
            raise ValueError(f"risk must be one of {RISK_LEVELS}, got {self.risk!r}")
        if self.budget not in BUDGET_LEVELS:
            raise ValueError(f"budget must be one of {BUDGET_LEVELS}, got {self.budget!r}")
        object.__setattr__(self, "rationale", tuple(self.rationale))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        schema_version = data.pop("schema_version")
        return {
            "schema_version": schema_version,
            **data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyRecommendation":
        return cls(
            model_name=data["model_name"],
            capability_average=data["capability_average"],
            risk=data.get("risk", "medium"),
            budget=data.get("budget", "standard"),
            policy=HarnessPolicy.from_dict(data["policy"]),
            rationale=tuple(data.get("rationale", ())),
            source=data.get("source", "rule_based"),
            profile_schema_version=data.get("profile_schema_version", "unknown"),
            schema_version=data.get("schema_version", "0.2"),
        )


def load_policy_recommendation(path: Path) -> PolicyRecommendation:
    return PolicyRecommendation.from_dict(json.loads(path.read_text(encoding="utf-8")))
