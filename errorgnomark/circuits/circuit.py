# # File Path: errorgnomark/circuits/circuit.py
# # This is the "golden" version that merges your advanced features with the required compatibility methods.

# import numpy as np
# from typing import List, Tuple, Any, Dict, Optional

# class Gate:
#     """Represents a single quantum gate operation as a class."""
#     def __init__(self, name: str, qubits: Tuple[int, ...], params: List[Any] = None):
#         self.name = name
#         self.qubits = qubits
#         self.params = params if params is not None else []

#     def inverse(self) -> 'Gate':
#         """Calculates the Hermitian conjugate (dagger/inverse) of this Gate."""
#         if self.name.lower() in ['h', 'x', 'y', 'z', 'cnot', 'cz', 'iswap']:
#             new_name = self.name
#         elif self.name.endswith('dg'):
#             new_name = self.name[:-2]
#         else:
#             new_name = f"{self.name}dg"
#         return Gate(name=new_name, qubits=self.qubits, params=self.params)

#     def __repr__(self) -> str:
#         return f"Gate(name='{self.name}', qubits={self.qubits}, params={self.params})"


# class QuantumCircuit:
#     """A basic, framework-agnostic data structure for a quantum circuit."""
#     # --- [MODIFICATION 1: FLEXIBLE CONSTRUCTOR] ---
#     # We make `gates` an optional argument. If not provided, it creates an empty circuit.
#     def __init__(self, qubits: List[int], gates: Optional[List[Gate]] = None):
#         if not qubits:
#             raise ValueError("QuantumCircuit must be initialized with a list of qubit indices.")
#         self.qubits = qubits
#         self.gates = gates if gates is not None else []
#         self.num_qubits = len(qubits) # Added for convenience

#     def __repr__(self) -> str:
#         gate_strs = [f"{g.name}{g.qubits}" for g in self.gates]
#         return (
#             f"QuantumCircuit(qubits={self.qubits}, num_gates={len(self.gates)})\n"
#             f"Gates: " + " -> ".join(gate_strs)
#         )

#     # --- [MODIFICATION 2: ADDED `add_gate` METHOD] ---
#     def add_gate(self, gate: Gate):
#         """Adds a gate to the end of the circuit."""
#         self.gates.append(gate)

#     # --- [MODIFICATION 3: ADDED `measure_all` METHOD] ---
#     def measure_all(self):
#         """Adds measurement operations to all qubits defined in the circuit."""
#         # Note: This assumes measurement is a conceptual gate.
#         # The backend simulator will interpret this.
#         for q_index in self.qubits:
#             self.add_gate(Gate('measure', (q_index,)))

#     # --- [MODIFICATION 4: ADDED THE CRITICAL `copy` METHOD] ---
#     def copy(self) -> 'QuantumCircuit':
#         """
#         Creates a shallow copy of the quantum circuit.
#         This is essential for algorithms like tomography.
#         """
#         # Create new lists for gates and qubits to ensure the copy is independent.
#         new_gates = self.gates[:]
#         new_qubits = self.qubits[:]
#         return QuantumCircuit(qubits=new_qubits, gates=new_gates)

#     def __add__(self, other: 'QuantumCircuit') -> 'QuantumCircuit':
#         """Concatenates this circuit with another circuit."""
#         if not isinstance(other, QuantumCircuit):
#             return NotImplemented
#         combined_qubits: List[int] = sorted(list(set(self.qubits) | set(other.qubits)))
#         combined_gates: List[Gate] = self.gates + other.gates
#         return QuantumCircuit(qubits=combined_qubits, gates=combined_gates)


# # GATE_MATRIX_MAP and helper functions remain unchanged.
# GATE_MATRIX_MAP: Dict[str, np.ndarray] = {
#     'id': np.eye(2, dtype=complex),
#     'h': np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),
#     'x': np.array([[0, 1], [1, 0]], dtype=complex),
#     'y': np.array([[0, -1j], [1j, 0]], dtype=complex),
#     'z': np.array([[1, 0], [0, -1]], dtype=complex),
#     's': np.array([[1, 0], [0, 1j]], dtype=complex),
#     'sdg': np.array([[1, 0], [0, -1j]], dtype=complex),
#     't': np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex),
#     'tdg': np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex),
#     'sqrtx': np.array([[0.5+0.5j, 0.5-0.5j], [0.5-0.5j, 0.5+0.5j]], dtype=complex),
#     'sqrty': np.array([[0.5+0.5j, -0.5-0.5j], [0.5+0.5j, 0.5+0.5j]], dtype=complex),
#     'cnot': np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex),
#     'cz': np.array([[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,-1]], dtype=complex),
#     'iswap': np.array([[1,0,0,0], [0,0,1j,0], [0,1j,0,0], [0,0,0,1]], dtype=complex)
# }

# def get_matrix(gate_name: str) -> np.ndarray:
#     """Retrieves the matrix for a given gate name, handling daggers automatically."""
#     lookup_name = gate_name.lower()
#     matrix = GATE_MATRIX_MAP.get(lookup_name)
#     if matrix is not None:
#         return matrix
#     if lookup_name.endswith('dg'):
#         base_name = lookup_name[:-2]
#         base_matrix = GATE_MATRIX_MAP.get(base_name)
#         if base_matrix is not None:
#             return base_matrix.conj().T
#     raise ValueError(f"Matrix for gate '{gate_name}' not found in GATE_MATRIX_MAP.")

# def get_dagger(gate: Gate) -> Gate:
#     """[DEPRECATED] Use gate.inverse() instead."""
#     return gate.inverse()
# File Path: errorgnomark/circuits/circuit.py
# MODIFIED: Gate.inverse() is now more robust and case-insensitive for standard gates.

import numpy as np
from typing import List, Tuple, Any, Dict, Optional

class Gate:
    """Represents a single quantum gate operation as a class."""
    def __init__(self, name: str, qubits: Tuple[int, ...], params: List[Any] = None):
        self.name = name
        self.qubits = qubits
        self.params = params if params is not None else []

    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    # [[[ MODIFIED Gate.inverse() METHOD FOR ROBUSTNESS ]]]
    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    def inverse(self) -> 'Gate':
        """
        Calculates the Hermitian conjugate (dagger/inverse) of this Gate.
        This method is case-insensitive for standard gate names.
        """
        lower_name = self.name.lower()

        # Explicit inverse pairs (handles 's'/'sdg', 't'/'tdg', etc.)
        inverse_pairs = {
            's': 'sdg', 'sdg': 's',
            't': 'tdg', 'tdg': 't',
            'rx90': 'rxm90', 'rxm90': 'rx90',
            'ry90': 'rym90', 'rym90': 'ry90',
        }
        if lower_name in inverse_pairs:
            return Gate(name=inverse_pairs[lower_name], qubits=self.qubits, params=self.params)

        # Self-inverse gates (H, X, Y, Z, CNOT, etc.)
        self_inverse_gates = [
            'h', 'x', 'y', 'z', 'cnot', 'cz', 'iswap', 'swap',
            'ccnot', 'toffoli', 'cswap', 'fredkin', 'ccz', 'ecr'
        ]
        if lower_name in self_inverse_gates:
            # Return a new gate with the same name to preserve original casing if desired
            return Gate(name=self.name, qubits=self.qubits, params=self.params)

        # Generic fallback for names ending in 'dg'
        if lower_name.endswith('dg'):
            # Return the base name, e.g., 'mydg' -> 'my'
            base_name = self.name[:-2]
            return Gate(name=base_name, qubits=self.qubits, params=self.params)
        
        # Generic fallback for all other gates
        # e.g., 'mygate' -> 'mygatedg'
        return Gate(name=f"{self.name}dg", qubits=self.qubits, params=self.params)
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    def __repr__(self) -> str:
        return f"Gate(name='{self.name}', qubits={self.qubits}, params={self.params})"


class QuantumCircuit:
    """A basic, framework-agnostic data structure for a quantum circuit."""
    def __init__(self, qubits: List[int], gates: Optional[List[Gate]] = None):
        if not qubits:
            raise ValueError("QuantumCircuit must be initialized with a list of qubit indices.")
        self.qubits = qubits
        self.gates = gates if gates is not None else []
        self.num_qubits = len(qubits)

    def __repr__(self) -> str:
        gate_strs = [f"{g.name}{g.qubits}" for g in self.gates]
        return (
            f"QuantumCircuit(qubits={self.qubits}, num_gates={len(self.gates)})\n"
            f"Gates: " + " -> ".join(gate_strs)
        )

    def add_gate(self, gate: Gate):
        """Adds a gate to the end of the circuit."""
        self.gates.append(gate)

    def measure_all(self):
        """Adds measurement operations to all qubits defined in the circuit."""
        for q_index in self.qubits:
            self.add_gate(Gate('measure', (q_index,)))

    def copy(self) -> 'QuantumCircuit':
        """Creates a shallow copy of the quantum circuit."""
        new_gates = self.gates[:]
        new_qubits = self.qubits[:]
        return QuantumCircuit(qubits=new_qubits, gates=new_gates)

    def __add__(self, other: 'QuantumCircuit') -> 'QuantumCircuit':
        """Concatenates this circuit with another circuit."""
        if not isinstance(other, QuantumCircuit):
            return NotImplemented
        combined_qubits: List[int] = sorted(list(set(self.qubits) | set(other.qubits)))
        combined_gates: List[Gate] = self.gates + other.gates
        return QuantumCircuit(qubits=combined_qubits, gates=combined_gates)


# GATE_MATRIX_MAP and other functions remain unchanged.
GATE_MATRIX_MAP: Dict[str, np.ndarray] = {
    'id': np.eye(2, dtype=complex), 'h': np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),
    'x': np.array([[0, 1], [1, 0]], dtype=complex), 'y': np.array([[0, -1j], [1j, 0]], dtype=complex),
    'z': np.array([[1, 0], [0, -1]], dtype=complex), 's': np.array([[1, 0], [0, 1j]], dtype=complex),
    'sdg': np.array([[1, 0], [0, -1j]], dtype=complex), 't': np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex),
    'tdg': np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex),
    'sqrtx': np.array([[0.5+0.5j, 0.5-0.5j], [0.5-0.5j, 0.5+0.5j]], dtype=complex),
    'sqrty': np.array([[0.5+0.5j, -0.5-0.5j], [0.5+0.5j, 0.5+0.5j]], dtype=complex),
    'rx90': np.array([[1, -1j], [-1j, 1]], dtype=complex) / np.sqrt(2),
    'rxm90': np.array([[1, 1j], [1j, 1]], dtype=complex) / np.sqrt(2),
    'ry90': np.array([[1, -1], [1, 1]], dtype=complex) / np.sqrt(2),
    'rym90': np.array([[1, 1], [-1, 1]], dtype=complex) / np.sqrt(2),
    'cnot': np.array([[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]], dtype=complex),
    'cz': np.array([[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,-1]], dtype=complex),
    'iswap': np.array([[1,0,0,0], [0,0,1j,0], [0,1j,0,0], [0,0,0,1]], dtype=complex),
    'swap': np.array([[1,0,0,0], [0,0,1,0], [0,1,0,0], [0,0,0,1]], dtype=complex),
    'ecr': np.array([[0,1,0,1j], [1,0,-1j,0], [0,-1j,0,1], [1j,0,1,0]], dtype=complex) / np.sqrt(2),
    'ccnot': np.array([[1,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0], [0,0,1,0,0,0,0,0], [0,0,0,1,0,0,0,0], [0,0,0,0,1,0,0,0], [0,0,0,0,0,1,0,0], [0,0,0,0,0,0,0,1], [0,0,0,0,0,0,1,0]], dtype=complex),
    'toffoli': np.array([[1,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0], [0,0,1,0,0,0,0,0], [0,0,0,1,0,0,0,0], [0,0,0,0,1,0,0,0], [0,0,0,0,0,1,0,0], [0,0,0,0,0,0,0,1], [0,0,0,0,0,0,1,0]], dtype=complex),
    'cswap': np.array([[1,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0], [0,0,1,0,0,0,0,0], [0,0,0,1,0,0,0,0], [0,0,0,0,1,0,0,0], [0,0,0,0,0,0,1,0], [0,0,0,0,0,1,0,0], [0,0,0,0,0,0,0,1]], dtype=complex),
    'fredkin': np.array([[1,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0], [0,0,1,0,0,0,0,0], [0,0,0,1,0,0,0,0], [0,0,0,0,1,0,0,0], [0,0,0,0,0,0,1,0], [0,0,0,0,0,1,0,0], [0,0,0,0,0,0,0,1]], dtype=complex),
    'ccz': np.array([[1,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0], [0,0,1,0,0,0,0,0], [0,0,0,1,0,0,0,0], [0,0,0,0,1,0,0,0], [0,0,0,0,0,1,0,0], [0,0,0,0,0,0,1,0], [0,0,0,0,0,0,0,-1]], dtype=complex),
}

def get_matrix(gate_name: str) -> np.ndarray:
    lookup_name = gate_name.lower()
    matrix = GATE_MATRIX_MAP.get(lookup_name)
    if matrix is not None:
        return matrix
    if lookup_name.endswith('dg'):
        base_name = lookup_name[:-2]
        base_matrix = GATE_MATRIX_MAP.get(base_name)
        if base_matrix is not None:
            return base_matrix.conj().T
    raise ValueError(f"Matrix for gate '{gate_name}' not found in GATE_MATRIX_MAP.")

def get_dagger(gate: Gate) -> Gate:
    """[DEPRECATED] Use gate.inverse() instead."""
    return gate.inverse()