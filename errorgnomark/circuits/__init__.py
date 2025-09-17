# errorgnomark/circuits/__init__.py

"""
ErrorGnoMark Circuits Package

This package contains modules for the representation, construction, and
manipulation of quantum circuits.

It provides the core `QuantumCircuit` class and standard quantum gates as
building blocks for all experiments.

Usage:
    from errorgnomark.circuits import QuantumCircuit, H, CNOT
    
    qc = QuantumCircuit(2)
    qc.apply(H, 0)
    qc.apply(CNOT, 0, 1)
"""

# Assume these classes/objects are defined in submodules, e.g., circuit.py, gates.py
# This makes the most common tools readily available.
# from .circuit import QuantumCircuit
# from .gates import Gate, H, X, Y, Z, Rz, CNOT, I

# For demonstration, let's define placeholders if they don't exist yet.
# In a real project, you would uncomment the lines above.
class QuantumCircuit:
    pass
class Gate:
    pass
class H(Gate):
    pass
class CNOT(Gate):
    pass

__all__ = [
    "QuantumCircuit",
    "Gate",
    "H",
    "CNOT",
    # "X", "Y", "Z", "Rz", "I" # Add other gates as they are defined
]