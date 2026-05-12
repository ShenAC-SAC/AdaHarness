from __future__ import annotations

from dataclasses import dataclass, field
from os import environ
from pathlib import Path
from typing import Any

from adaharness.models import ModelConfig, build_model_config
from adaharness.models.base import ProviderName
from adaharness.policies.schema import BudgetLevel, RiskLevel

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10 in CI.
    import tomli as tomllib


@dataclass(frozen=True)
class ProviderConfig:
    type: ProviderName
    base_url: str | None = None
    api_key_env: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderConfig":
        return cls(
            type=data.get("type", "synthetic"),
            base_url=data.get("base_url"),
            api_key_env=data.get("api_key_env"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "base_url": self.base_url,
            "api_key_env": self.api_key_env,
            "api_key_configured": bool(self.api_key_env and environ.get(self.api_key_env)),
        }


@dataclass(frozen=True)
class ModelEntry:
    provider: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelEntry":
        return cls(provider=data["provider"])


@dataclass(frozen=True)
class ConfigDefaults:
    risk: RiskLevel = "medium"
    budget: BudgetLevel = "standard"
    taskset: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfigDefaults":
        return cls(
            risk=data.get("risk", "medium"),
            budget=data.get("budget", "standard"),
            taskset=data.get("taskset"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk": self.risk,
            "budget": self.budget,
            "taskset": self.taskset,
        }


@dataclass(frozen=True)
class AdaHarnessConfig:
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    models: dict[str, ModelEntry] = field(default_factory=dict)
    defaults: ConfigDefaults = field(default_factory=ConfigDefaults)
    source_path: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, source_path: str | None = None) -> "AdaHarnessConfig":
        return cls(
            providers={
                name: ProviderConfig.from_dict(provider)
                for name, provider in data.get("providers", {}).items()
            },
            models={
                name: ModelEntry.from_dict(model)
                for name, model in data.get("models", {}).items()
            },
            defaults=ConfigDefaults.from_dict(data.get("defaults", {})),
            source_path=source_path,
        )

    def resolve_model(self, model_name: str) -> ModelConfig:
        if model_name not in self.models:
            raise ValueError(f"Model {model_name!r} is not defined in config")
        model = self.models[model_name]
        if model.provider not in self.providers:
            raise ValueError(f"Provider {model.provider!r} for model {model_name!r} is not defined")
        provider = self.providers[model.provider]
        api_key = environ.get(provider.api_key_env) if provider.api_key_env else None
        return build_model_config(
            model_name,
            provider=provider.type,
            base_url=provider.base_url,
            api_key=api_key,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "providers": {
                name: provider.to_dict()
                for name, provider in self.providers.items()
            },
            "models": {
                name: {"provider": model.provider}
                for name, model in self.models.items()
            },
            "defaults": self.defaults.to_dict(),
        }


def load_config(path: str | Path, *, env_file: str | Path | None = None) -> AdaHarnessConfig:
    config_path = Path(path)
    dotenv_path = Path(env_file) if env_file else config_path.parent / ".env"
    load_env_file(dotenv_path)
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    return AdaHarnessConfig.from_dict(data, source_path=str(config_path))


def load_env_file(path: str | Path) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        environ.setdefault(key.strip(), _clean_env_value(value.strip()))


def _clean_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
