from __future__ import annotations

from dataclasses import dataclass, field

from adaharness.harnesses.modular import ModularHarness
from adaharness.modules import DEFAULT_MODULE_REGISTRY, ModuleRegistry
from adaharness.policies.schema import HarnessPolicy
from adaharness.specs.harness_spec import HarnessSpec


@dataclass(frozen=True)
class HarnessBuilder:
    registry: ModuleRegistry = field(default_factory=lambda: DEFAULT_MODULE_REGISTRY)

    def build(self, spec: HarnessSpec) -> ModularHarness:
        source_policy = spec.source_policy or spec.metadata.get("source_policy")
        if not isinstance(source_policy, dict):
            raise ValueError("HarnessSpec metadata.source_policy is required")
        modules = tuple(self.registry.create(module_spec) for module_spec in spec.modules if module_spec.enabled)
        return ModularHarness(
            name=spec.name,
            policy=HarnessPolicy.from_dict(source_policy),
            spec=spec,
            modules=modules,
            registry=self.registry,
        )
