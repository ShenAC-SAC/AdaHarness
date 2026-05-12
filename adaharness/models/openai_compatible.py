from __future__ import annotations

from dataclasses import dataclass, field
from os import getenv
from typing import Any

from adaharness.models.base import Message, ModelConfig, ModelResponse, ModelUsage, ToolSpec


def openai_compatible_config(name: str, base_url: str | None = None) -> ModelConfig:
    return ModelConfig(name=name, provider="openai-compatible", base_url=base_url)


@dataclass
class OpenAICompatibleModelClient:
    model_name: str
    base_url: str | None = None
    api_key: str | None = None
    _client: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "OpenAI-compatible models require the optional dependency: "
                'uv sync --extra openai --group dev'
            ) from exc

        self._client = OpenAI(api_key=self.api_key or getenv("OPENAI_API_KEY"), base_url=self.base_url)

    def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list[ToolSpec] | None = None,
    ) -> ModelResponse:
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if tools is not None:
            kwargs["tools"] = tools

        raw = self._client.chat.completions.create(**kwargs)
        text = raw.choices[0].message.content or ""
        usage = None
        if raw.usage is not None:
            usage = ModelUsage(
                input_tokens=raw.usage.prompt_tokens,
                output_tokens=raw.usage.completion_tokens,
                total_tokens=raw.usage.total_tokens,
            )
        return ModelResponse(text=text, raw=raw, usage=usage)
