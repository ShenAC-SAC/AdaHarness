from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


CAPABILITY_FIELDS = (
    "planning",
    "tool_use",
    "instruction_following",
    "self_verification",
    "context_management",
    "recovery",
    "cost_sensitivity",
    "delegation",
)


@dataclass(frozen=True)
class CapabilityScore:
    name: str
    score: float
    confidence: float
    evidence: tuple[str, ...] = ()
    failed_cases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_unit_interval("score", self.score)
        _validate_unit_interval("confidence", self.confidence)
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "failed_cases", tuple(self.failed_cases))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityScore":
        return cls(
            name=data["name"],
            score=data["score"],
            confidence=data["confidence"],
            evidence=tuple(data.get("evidence", ())),
            failed_cases=tuple(data.get("failed_cases", ())),
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
    delegation: float = 0.5
    scores: dict[str, CapabilityScore] = field(default_factory=dict)
    weaknesses: tuple[str, ...] = ()
    recommended_controls: tuple[str, ...] = ()
    schema_version: str = "0.3"

    def __post_init__(self) -> None:
        for field_name in CAPABILITY_FIELDS:
            _validate_unit_interval(field_name, getattr(self, field_name))

        scores = self.scores or {
            field_name: CapabilityScore(
                name=field_name,
                score=getattr(self, field_name),
                confidence=0.5,
                evidence=("synthetic default estimate",),
            )
            for field_name in CAPABILITY_FIELDS
        }
        normalized_scores = {
            name: score if isinstance(score, CapabilityScore) else CapabilityScore.from_dict(score)
            for name, score in scores.items()
        }
        object.__setattr__(self, "scores", normalized_scores)
        object.__setattr__(self, "weaknesses", tuple(self.weaknesses))
        object.__setattr__(self, "recommended_controls", tuple(self.recommended_controls))

    @property
    def capability_average(self) -> float:
        return sum(getattr(self, field) for field in CAPABILITY_FIELDS) / len(CAPABILITY_FIELDS)

    def score_for(self, name: str) -> CapabilityScore:
        if name not in self.scores:
            raise KeyError(f"unknown capability score: {name}")
        return self.scores[name]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        schema_version = data.pop("schema_version")
        return {
            "schema_version": schema_version,
            **data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelProfile":
        scores = {
            name: CapabilityScore.from_dict(score)
            for name, score in data.get("scores", {}).items()
        }
        kwargs = {field_name: data[field_name] for field_name in CAPABILITY_FIELDS if field_name in data}
        for field_name, score in scores.items():
            kwargs.setdefault(field_name, score.score)
        return cls(
            model_name=data["model_name"],
            scores=scores,
            weaknesses=tuple(data.get("weaknesses", ())),
            recommended_controls=tuple(data.get("recommended_controls", ())),
            schema_version=data.get("schema_version", "0.3"),
            **kwargs,
        )


def _validate_unit_interval(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0, got {value!r}")
