# errorgnomark/backends/__init__.py

"""
ErrorGnoMark Backends Package

This package provides the abstractions for executing quantum circuits on various
quantum processing units (QPUs) and simulators.

The core component is the `BaseBackend`, an abstract base class that defines the
common interface all backend implementations must adhere to.

Usage:
    from errorgnomark.backends import BaseBackend

    class MySimulatorBackend(BaseBackend):
        def run_circuits(self, circuits, shots):
            # ... implementation ...
            pass
"""

# Import the base class to make it directly accessible from the package root.
from .base_backend import BaseBackend

__all__ = [
    "BaseBackend"
]