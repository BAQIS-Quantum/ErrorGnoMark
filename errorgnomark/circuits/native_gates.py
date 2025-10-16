# File Path: errorgnomark/circuits/native_gates.py

"""
A collection of native gate sets for various quantum computing platforms.

This module provides static lists of gate names that represent the fundamental,
indivisible physical operations (native gates) available on different hardware.
These lists are intended to be used as compilation targets for the
`QuantumCircuit.decompose` method.

This is distinct from `gate_sets.py`, which contains classes for dynamically
generating complex gate sequences for specific experiments.
"""
from typing import List, Dict

# --- Superconducting Qubit Native Gates ---

# Native gates for typical CNOT-based platforms (e.g., IBM Quantum)
IBM_Q_NATIVE_GATES: List[str] = [
    'cnot', 'sx', 'x', 'rz', 'id'
]

# Native gates for typical CZ-based platforms (e.g., Rigetti, Google)
SUPERCONDUCTING_CZ_NATIVE_GATES: List[str] = [
    'cz', 'h', 's', 'sdg', 't', 'tdg', 'x', 'y', 'z', 'id',
    'rx90', 'rxm90', 'ry90', 'rym90', 'sqrtx'
]

# --- Trapped Ion Native Gates ---

# Native gates for typical trapped-ion platforms using two-qubit rotations
# (e.g., IonQ, Quantinuum)
TRAPPED_ION_NATIVE_GATES: List[str] = [
    'rxx', 'ryy', 'rzz', 'rx', 'ry', 'rz', 's', 'sdg', 't', 'tdg', 'id'
]


# --- Central Dictionary for Easy Access ---

# A convenient dictionary to access all standard native gate sets by a simple name.
# This is useful for users and backends to easily reference a standard configuration.
STANDARD_NATIVE_GATES: Dict[str, List[str]] = {
    "ibm": IBM_Q_NATIVE_GATES,
    "rigetti": SUPERCONDUCTING_CZ_NATIVE_GATES,
    "google": SUPERCONDUCTING_CZ_NATIVE_GATES,
    "ionq": TRAPPED_ION_NATIVE_GATES,
}