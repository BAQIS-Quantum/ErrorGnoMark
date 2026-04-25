# File Path: errorgnomark/circuits/__init__.py
# This file makes the 'circuits' directory a Python package and exposes
# its key components for easier importing.

from .circuit import (
    Gate,
    QuantumCircuit,
    get_matrix,
    get_parameterized_matrix,
    get_dagger
)
# from .visualization import draw_circuit_text

# This allows other parts of the program to write:
# from egm.core.circuits import QuantumCircuit
# instead of the longer:
# from egm.core.circuits.circuit import QuantumCircuit

__all__ = [
    "Gate",
    "QuantumCircuit",
    "get_matrix",
    "get_parameterized_matrix",
    "get_dagger",
]