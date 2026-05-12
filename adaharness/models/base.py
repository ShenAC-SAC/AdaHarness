from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelConfig:
    name: str
    provider: str = "manual"
    base_url: str | None = None


class ModelAdapter(Protocol):
    config: ModelConfig

    def complete(self, prompt: str) -> str:
        """Return a model completion for a prompt."""
