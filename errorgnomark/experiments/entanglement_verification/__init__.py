# errorgnomark/experiments/entanglement_verification/__init__.py

"""
Entanglement Verification Module
================================

This package provides a suite of experiments for generating and verifying
standard entangled states, such as Bell, GHZ, and W states.

The primary classes are:
- BellStateVerification: For verifying 2-qubit Bell states.
- GHZStateVerification: For verifying N-qubit Greenberger-Horne-Zeilinger (GHZ) states.
- WStateVerification: For verifying N-qubit W states.

These classes follow a unified API, inheriting from a common base class,
allowing for consistent setup, execution, and analysis.
"""

from .bell_state import BellStateVerification
from .ghz_state import GHZStateVerification
from .w_state import WStateVerification

# Expose the main classes for easy access
__all__ = [
    "BellStateVerification",
    "GHZStateVerification",
    "WStateVerification",
]