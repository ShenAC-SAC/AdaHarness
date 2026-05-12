from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

from adaharness.profiler.profile_schema import CAPABILITY_FIELDS


@dataclass(frozen=True)
class ProfilerRubric:
    success_criteria: tuple[str, ...] = ()
    expected_signals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "success_criteria", tuple(self.success_criteria))
        object.__setattr__(self, "expected_signals", tuple(self.expected_signals))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfilerRubric":
        return cls(
            success_criteria=tuple(data.get("success_criteria", ())),
            expected_signals=tuple(data.get("expected_signals", ())),
        )


@dataclass(frozen=True)
class ProfilerTask:
    id: str
    capability: str
    prompt: str
    difficulty: float
    rubric: ProfilerRubric = ProfilerRubric()

    def __post_init__(self) -> None:
        if self.capability not in CAPABILITY_FIELDS:
            supported = ", ".join(CAPABILITY_FIELDS)
            raise ValueError(f"unsupported capability {self.capability!r}; expected one of: {supported}")
        if not 0.0 <= self.difficulty <= 1.0:
            raise ValueError(f"difficulty must be between 0.0 and 1.0, got {self.difficulty!r}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfilerTask":
        capability = data.get("capability", data.get("target_capability"))
        rubric_data = {
            "success_criteria": data.get("success_criteria", ()),
            "expected_signals": data.get("expected_signals", ()),
            **data.get("rubric", {}),
        }
        return cls(
            id=data["id"],
            capability=capability,
            prompt=data["prompt"],
            difficulty=data["difficulty"],
            rubric=ProfilerRubric.from_dict(rubric_data),
        )


def load_profiler_task(path: Path) -> ProfilerTask:
    return ProfilerTask.from_dict(json.loads(path.read_text(encoding="utf-8")))


def load_profiler_taskset(path: Path) -> list[ProfilerTask]:
    if path.is_file():
        return [load_profiler_task(path)]
    return [load_profiler_task(task_path) for task_path in sorted(path.glob("*.json"))]
