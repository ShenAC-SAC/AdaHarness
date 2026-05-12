from __future__ import annotations

from dataclasses import dataclass

from adaharness.policies.schema import HarnessPolicy


@dataclass(frozen=True)
class Harness:
    name: str
    policy: HarnessPolicy

    @property
    def complexity_weight(self) -> float:
        weights = {
            "none": 0.0,
            "light": 0.2,
            "explicit": 0.45,
            "strict": 0.7,
            "moderate": 0.35,
            "selective": 0.35,
            "always": 0.7,
            "bounded": 0.35,
            "aggressive": 0.65,
            "small": 0.6,
            "medium": 0.35,
            "large": 0.1,
            "disabled": 0.0,
            "optional": 0.2,
            "recommended": 0.45,
            "mandatory": 0.7,
            "raw": 0.0,
            "summarized": 0.25,
            "retrieval_augmented": 0.45,
        }
        values = self.policy.to_dict().values()
        return sum(weights[value] for value in values) / len(self.policy.to_dict())
