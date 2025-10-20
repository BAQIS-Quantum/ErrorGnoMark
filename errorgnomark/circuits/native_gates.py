# File Path: errorgnomark/circuits/native_gates.py

"""
A collection of native gate sets for various quantum computing platforms.

This module provides static lists of gate names that represent the fundamental,
indivisible physical operations (native gates) available on different hardware.
These lists are intended to be used as compilation targets for the
`QuantumCircuit.decompose` method.

It also provides an interface for users to register their own custom native gate sets.

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
# This is mutable and can be extended using the `register_native_gate_set` function.
STANDARD_NATIVE_GATES: Dict[str, List[str]] = {
    "ibm": IBM_Q_NATIVE_GATES,
    "rigetti": SUPERCONDUCTING_CZ_NATIVE_GATES,
    "google": SUPERCONDUCTING_CZ_NATIVE_GATES,
    "ionq": TRAPPED_ION_NATIVE_GATES,
}

# --- User-Defined Gate Set Interface ---

def register_native_gate_set(name: str, gates: List[str], overwrite: bool = False):
    """
    Registers a new custom native gate set or updates an existing one.

    This function allows users to add their own hardware-specific gate sets
    to the central `STANDARD_NATIVE_GATES` dictionary, making them easily
    accessible for circuit decomposition.

    Args:
        name (str): The name for the new gate set (e.g., 'my_custom_qpu').
                    Names should be lowercase strings.
        gates (List[str]): A list of gate names (strings) that constitute
                           the native gate set.
        overwrite (bool, optional): If True, allows overwriting an existing
                                    gate set with the same name. If False
                                    (default), raises a ValueError if the
                                    name already exists.

    Raises:
        TypeError: If `name` is not a string or `gates` is not a list of strings.
        ValueError: If `name` is an empty string, or if the name already
                    exists and `overwrite` is False.
    """
    if not isinstance(name, str):
        raise TypeError(f"Gate set name must be a string, but got {type(name)}.")
    if not name:
        raise ValueError("Gate set name cannot be an empty string.")
    
    if not isinstance(gates, list) or not all(isinstance(g, str) for g in gates):
        raise TypeError("Gates must be provided as a list of strings.")

    name = name.lower() # Standardize to lowercase

    if name in STANDARD_NATIVE_GATES and not overwrite:
        raise ValueError(
            f"Gate set '{name}' already exists. Use `overwrite=True` to replace it."
        )

    STANDARD_NATIVE_GATES[name] = gates
    print(f"Successfully registered native gate set: '{name}'")