from __future__ import annotations

from dataclasses import dataclass, field
from os import getenv
from typing import Any

from adaharness.models.base import Message, ModelConfig, ModelResponse, ModelUsage, ToolSpec


def anthropic_config(name: str) -> ModelConfig:
    return ModelConfig(name=name, provider="anthropic")


@dataclass
class AnthropicModelClient:
    model_name: str
    api_key: str | None = None
    _client: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ImportError(
                "Anthropic models require the optional dependency: "
                'uv sync --extra anthropic --group dev'
            ) from exc

        self._client = Anthropic(api_key=self.api_key or getenv("ANTHROPIC_API_KEY"))

    def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list[ToolSpec] | None = None,
    ) -> ModelResponse:
        system_parts = [message["content"] for message in messages if message.get("role") == "system"]
        conversation = [message for message in messages if message.get("role") != "system"]
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": conversation,
            "max_tokens": max_tokens or 1024,
            "temperature": temperature,
        }
        if system_parts:
            kwargs["system"] = "\n\n".join(system_parts)
        if tools is not None:
            kwargs["tools"] = tools

        raw = self._client.messages.create(**kwargs)
        text = _anthropic_text(raw.content)
        usage = None
        if raw.usage is not None:
            usage = ModelUsage(
                input_tokens=raw.usage.input_tokens,
                output_tokens=raw.usage.output_tokens,
                total_tokens=raw.usage.input_tokens + raw.usage.output_tokens,
            )
        return ModelResponse(text=text, raw=raw, usage=usage)


def _anthropic_text(content: list[Any]) -> str:
    parts: list[str] = []
    for block in content:
        text = getattr(block, "text", None)
        if text is not None:
            parts.append(text)
    return "".join(parts)
