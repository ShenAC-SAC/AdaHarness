from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Budget:
    max_steps: int = 8
    max_tool_calls: int = 4
    max_retries: int = 2
    max_tokens: int = 8_000
