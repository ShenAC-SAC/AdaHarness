from __future__ import annotations

from typing import cast, get_args

from adaharness.models.anthropic import AnthropicModelClient
from adaharness.models.base import ModelClient, ModelConfig, ProviderName
from adaharness.models.local import LocalHTTPModelClient
from adaharness.models.mock import MockModelClient
from adaharness.models.openai_compatible import OpenAICompatibleModelClient


SUPPORTED_PROVIDERS = get_args(ProviderName)
_LOCAL_BASE_URL = "http://localhost:11434"


def build_model_config(
    model_name: str,
    *,
    provider: str = "synthetic",
    base_url: str | None = None,
) -> ModelConfig:
    if provider not in SUPPORTED_PROVIDERS:
        supported = ", ".join(SUPPORTED_PROVIDERS)
        raise ValueError(f"Unsupported provider {provider!r}. Expected one of: {supported}")
    return ModelConfig(name=model_name, provider=cast(ProviderName, provider), base_url=base_url)


def build_model_client(config: ModelConfig) -> ModelClient:
    if config.provider in {"synthetic", "mock"}:
        return MockModelClient(model_name=config.name)
    if config.provider == "openai-compatible":
        return OpenAICompatibleModelClient(model_name=config.name, base_url=config.base_url)
    if config.provider == "anthropic":
        return AnthropicModelClient(model_name=config.name)
    if config.provider == "local":
        return LocalHTTPModelClient(model_name=config.name, base_url=config.base_url or _LOCAL_BASE_URL)

    supported = ", ".join(SUPPORTED_PROVIDERS)
    raise ValueError(f"Unsupported provider {config.provider!r}. Expected one of: {supported}")
