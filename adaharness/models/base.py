from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol


ProviderName = Literal["synthetic", "mock", "openai-compatible", "anthropic", "local"]
Message = dict[str, str]
ToolSpec = dict[str, Any]


@dataclass(frozen=True)
class ModelConfig:
    name: str
    provider: ProviderName = "synthetic"
    base_url: str | None = None


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class ModelResponse:
    text: str
    raw: Any | None = None
    usage: ModelUsage | None = None


class ModelClient(Protocol):
    model_name: str

    def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list[ToolSpec] | None = None,
    ) -> ModelResponse:
        """Return a structured model completion."""


ModelAdapter = ModelClient
