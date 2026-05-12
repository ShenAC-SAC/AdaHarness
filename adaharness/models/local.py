from __future__ import annotations

from adaharness.models.base import ModelConfig


def local_config(name: str, base_url: str | None = None) -> ModelConfig:
    return ModelConfig(name=name, provider="local", base_url=base_url)
