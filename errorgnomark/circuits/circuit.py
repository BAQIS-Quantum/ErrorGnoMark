# File Path: errorgnomark/circuits/circuit.py
# [CORRECTED VERSION - Final Typo Fix]

import numpy as np
from typing import List, Tuple, Any, Dict, Optional

class Gate:
    """Represents a single quantum gate operation as a class."""
    def __init__(self, name: str, qubits: Tuple[int, ...], params: List[Any] = None):
        self.name = name
        self.qubits = qubits
        self.params = params if params is not None else []

    @property
    def arity(self) -> int:
        """Returns the number of qubits this gate acts on."""
        return len(self.qubits)

    def inverse(self) -> 'Gate':
        lower_name = self.name.lower()
        inverse_pairs = {
            's': 'sdg', 'sdg': 's', 't': 'tdg', 'tdg': 't',
            'rx90': 'rxm90', 'rxm90': 'rx90', 'ry90': 'rym90', 'rym90': 'ry90',
        }
        if lower_name in inverse_pairs:
            return Gate(name=inverse_pairs[lower_name], qubits=self.qubits, params=self.params)
        self_inverse_gates = [
            'h', 'x', 'y', 'z', 'cnot', 'cz', 'iswap', 'swap',
            'ccnot', 'toffoli', 'cswap', 'fredkin', 'ccz', 'ecr'
        ]
        if lower_name in self_inverse_gates:
            return Gate(name=self.name, qubits=self.qubits, params=self.params)
        if lower_name.endswith('dg'):
            base_name = self.name[:-2]
            return Gate(name=base_name, qubits=self.qubits, params=self.params)
        return Gate(name=f"{self.name}dg", qubits=self.qubits, params=self.params)

    def __repr__(self) -> str:
        return f"Gate(name='{self.name}', qubits={self.qubits}, params={self.params})"


class QuantumCircuit:
    """A basic, framework-agnostic data structure for a quantum circuit."""
    def __init__(self, qubits: List[int], gates: Optional[List[Gate]] = None):
        if not qubits:
            raise ValueError("QuantumCircuit must be initialized with a list of qubit indices.")
        self.qubits = sorted(qubits)
        self.gates = gates if gates is not None else []
        self.num_qubits = len(qubits)

    def __str__(self) -> str:
        """
        Provides a well-aligned, character-based string representation of the
        quantum circuit, similar to industry-standard libraries.
        """
        if not self.gates:
            return f"QuantumCircuit(qubits={self.qubits}, num_gates=0)"

        GATE_WIDTH = 7
        WIRE_SEGMENT = "-" * GATE_WIDTH
        CONTROL_SEGMENT = "--(*)--"
        TARGET_SEGMENT = "--(X)--"
        CONNECTION_SEGMENT = "--|--"
        lanes = {q: f"q{q}: " for q in self.qubits}

        for gate in self.gates:
            column_drawings = {}
            if gate.name == "measure":
                q = gate.qubits[0]
                column_drawings[q] = f"--[M]--"
            elif len(gate.qubits) == 1:
                q = gate.qubits[0]
                gate_name = gate.name.upper()[:3]
                column_drawings[q] = f"-|{gate_name:^3}|-"
            elif len(gate.qubits) == 2:
                q1, q2 = gate.qubits
                control, target = min(q1, q2), max(q1, q2)
                column_drawings[control] = CONTROL_SEGMENT
                column_drawings[target] = TARGET_SEGMENT
                for q_mid in range(control + 1, target):
                    if q_mid in self.qubits:
                        column_drawings[q_mid] = CONNECTION_SEGMENT
            
            for q in self.qubits:
                lanes[q] += column_drawings.get(q, WIRE_SEGMENT)

        header = f"QuantumCircuit(qubits={self.qubits}, num_gates={len(self.gates)})"
        circuit_drawing = "\n".join(lanes[q] for q in self.qubits)
        return f"{header}\n{circuit_drawing}"

    def __repr__(self) -> str:
        return f"QuantumCircuit(qubits={self.qubits}, num_gates={len(self.gates)})"

    def add_gate(self, gate: Gate):
        self.gates.append(gate)

    def measure_all(self):
        for q_index in self.qubits:
            self.add_gate(Gate('measure', (q_index,)))

    def copy(self) -> 'QuantumCircuit':
        new_gates = self.gates[:]
        new_qubits = self.qubits[:]
        return QuantumCircuit(qubits=new_qubits, gates=new_gates)

    def __add__(self, other: 'QuantumCircuit') -> 'QuantumCircuit':
        if not isinstance(other, QuantumCircuit):
            return NotImplemented
        combined_qubits: List[int] = sorted(list(set(self.qubits) | set(other.qubits)))
        combined_gates: List[Gate] = self.gates + other.gates
        return QuantumCircuit(qubits=combined_qubits, gates=combined_gates)

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
    # [FIX] Corrected the typo from 'dtye' to 'dtype'.
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