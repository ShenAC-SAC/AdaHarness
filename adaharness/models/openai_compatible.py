from __future__ import annotations

from adaharness.models.base import ModelConfig


def openai_compatible_config(name: str, base_url: str | None = None) -> ModelConfig:
    return ModelConfig(name=name, provider="openai-compatible", base_url=base_url)
