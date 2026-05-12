from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adaharness.models.base import Message, ModelConfig, ModelResponse, ModelUsage, ToolSpec


def local_config(name: str, base_url: str | None = None) -> ModelConfig:
    return ModelConfig(name=name, provider="local", base_url=base_url)


@dataclass
class LocalHTTPModelClient:
    model_name: str
    base_url: str = "http://localhost:11434"

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")

    def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tools: list[ToolSpec] | None = None,
    ) -> ModelResponse:
        try:
            import requests
        except ImportError as exc:
            raise ImportError(
                "Local HTTP models require the optional dependency: "
                'uv sync --extra local --group dev'
            ) from exc

        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        if tools is not None:
            payload["tools"] = tools

        raw = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
        raw.raise_for_status()
        data = raw.json()
        text = _extract_local_text(data)
        usage = ModelUsage(
            input_tokens=int(data.get("prompt_eval_count", 0)),
            output_tokens=int(data.get("eval_count", 0)),
            total_tokens=int(data.get("prompt_eval_count", 0)) + int(data.get("eval_count", 0)),
        )
        return ModelResponse(text=text, raw=data, usage=usage)


def _extract_local_text(data: dict[str, Any]) -> str:
    if "message" in data:
        return str(data["message"].get("content", ""))
    if "choices" in data:
        return str(data["choices"][0]["message"].get("content", ""))
    return str(data.get("response", ""))
