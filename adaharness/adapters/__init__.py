"""Experimental runtime-binding API.

The trace-first MVP does not require host projects to adopt runtime adapters.
Keep this package available for future binding experiments and compatibility
tests, but do not treat it as the primary user path.
"""

from adaharness.adapters.base import RuntimeAdapter
from adaharness.adapters.binding import AdapterCapabilities, RuntimeBinding
from adaharness.adapters.generic import GenericRuntimeAdapter, bind_runtime

__all__ = [
    "AdapterCapabilities",
    "GenericRuntimeAdapter",
    "RuntimeAdapter",
    "RuntimeBinding",
    "bind_runtime",
]
