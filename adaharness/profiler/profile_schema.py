from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CAPABILITY_FIELDS = (
    "planning",
    "tool_use",
    "instruction_following",
    "self_verification",
    "context_management",
    "recovery",
)


@dataclass(frozen=True)
class ModelProfile:
    model_name: str
    planning: float
    tool_use: float
    instruction_following: float
    self_verification: float
    context_management: float
    recovery: float
    cost_sensitivity: float = 0.5

    def __post_init__(self) -> None:
        for field in (*CAPABILITY_FIELDS, "cost_sensitivity"):
            value = getattr(self, field)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field} must be between 0.0 and 1.0, got {value!r}")

    @property
    def capability_average(self) -> float:
        return sum(getattr(self, field) for field in CAPABILITY_FIELDS) / len(CAPABILITY_FIELDS)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelProfile":
        return cls(**data)
