from adaharness.harnesses.base import Harness
from adaharness.policies.presets import STRUCTURED_POLICY

STRUCTURED_HARNESS = Harness(name="structured", policy=STRUCTURED_POLICY)
