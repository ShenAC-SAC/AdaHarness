from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


PlanningDepth = Literal["none", "light", "explicit", "strict"]
ToolGatekeeping = Literal["none", "moderate", "strict"]
VerifierStrength = Literal["none", "selective", "always"]
RetryPolicy = Literal["none", "bounded", "aggressive"]
AutonomyBudget = Literal["small", "medium", "large"]
SubagentPolicy = Literal["disabled", "optional", "recommended", "mandatory"]
ContextPolicy = Literal["raw", "summarized", "retrieval_augmented"]
RiskLevel = Literal["low", "medium", "high"]
BudgetLevel = Literal["constrained", "standard", "generous"]

RISK_LEVELS: tuple[RiskLevel, ...] = ("low", "medium", "high")
BUDGET_LEVELS: tuple[BudgetLevel, ...] = ("constrained", "standard", "generous")


@dataclass(frozen=True)
class HarnessPolicy:
    planning_depth: PlanningDepth
    tool_gatekeeping: ToolGatekeeping
    verifier_strength: VerifierStrength
    retry_policy: RetryPolicy
    autonomy_budget: AutonomyBudget
    subagent_policy: SubagentPolicy
    context_policy: ContextPolicy

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HarnessPolicy":
        return cls(**data)
