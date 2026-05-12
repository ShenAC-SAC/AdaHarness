from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class EvalTask:
    id: str
    category: str
    prompt: str
    difficulty: float
    target_capability: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.difficulty <= 1.0:
            raise ValueError(f"difficulty must be between 0.0 and 1.0, got {self.difficulty!r}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvalTask":
        return cls(**data)


def load_task(path: Path) -> EvalTask:
    return EvalTask.from_dict(json.loads(path.read_text(encoding="utf-8")))


def load_taskset(path: Path) -> list[EvalTask]:
    if path.is_file():
        return [load_task(path)]
    return [load_task(task_path) for task_path in sorted(path.glob("*.json"))]
