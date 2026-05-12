from __future__ import annotations

from dataclasses import dataclass, field

from adaharness.models.base import Message, ModelConfig, ModelResponse, ModelUsage, ToolSpec


def mock_config(name: str = "mock-model") -> ModelConfig:
    return ModelConfig(name=name, provider="mock")


@dataclass
class MockModelClient:
    model_name: str = "mock-model"
    responses: tuple[str, ...] = ("mock response",)
    _index: int = field(default=0, init=False, repr=False)

    def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list[ToolSpec] | None = None,
    ) -> ModelResponse:
        text = self._next_response(messages)
        output_tokens = len(text.split())
        input_tokens = sum(len(message.get("content", "").split()) for message in messages)
        usage = ModelUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
        raw = {
            "provider": "mock",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tool_count": len(tools or []),
        }
        return ModelResponse(text=text, raw=raw, usage=usage)

    def _next_response(self, messages: list[Message]) -> str:
        if self.responses:
            index = min(self._index, len(self.responses) - 1)
            self._index += 1
            return self.responses[index]

        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")
        return ""
