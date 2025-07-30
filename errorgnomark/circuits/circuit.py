# errorgnomark/circuits/circuit.py

from typing import List, Tuple, Any, NamedTuple

class Gate(NamedTuple):
    """
    Represents a single quantum gate operation.
    
    Attributes:
        name (str): The name of the gate (e.g., 'h', 'rx', 'cnot').
        qubits (Tuple[int, ...]): The qubit(s) the gate acts on.
        params (List[Any]): A list of parameters, like rotation angles.
    """
    name: str
    qubits: Tuple[int, ...]
    params: List[Any] = []


class QuantumCircuit:
    """
    A simple container for a sequence of quantum gates.
    """
    def __init__(self, num_qubits: int):
        if num_qubits < 1:
            raise ValueError("Number of qubits must be at least 1.")
        self.num_qubits = num_qubits
        self.gates: List[Gate] = []

    def add_gate(self, gate: Gate):
        """Adds a gate to the circuit."""
        self.gates.append(gate)

    def __repr__(self) -> str:
        gate_str = ", ".join([f"{g.name}{g.qubits}" for g in self.gates])
        return f"QuantumCircuit(num_qubits={self.num_qubits}, gates=[{gate_str}])"