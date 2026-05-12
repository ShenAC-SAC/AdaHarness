from __future__ import annotations

from adaharness.models.base import ModelConfig


def anthropic_config(name: str) -> ModelConfig:
    return ModelConfig(name=name, provider="anthropic")
