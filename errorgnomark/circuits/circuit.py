# errorgnomark/circuits/circuit.py
from typing import List, Tuple, NamedTuple, Any

# [DEFINITION]: Define the Gate class here.
# We use NamedTuple because it's a lightweight and immutable data container, perfect for this scenario.
class Gate(NamedTuple):
    """
    Represents a single quantum gate operation.
    
    Attributes:
        name (str): The name of the gate (e.g., 'h', 'cnot').
        qubits (Tuple[int, ...]): The qubit(s) the gate acts on.
        params (List[Any]): Optional parameters for the gate (e.g., rotation angles).
    """
    name: str
    qubits: Tuple[int, ...]
    params: List[Any] = []


class QuantumCircuit:
    """
    A basic, framework-agnostic data structure for a quantum circuit.
    """
    # [UPDATE]: The 'gates' attribute of QuantumCircuit is now a list of Gate objects.
    def __init__(self, qubits: List[int], gates: List[Gate]):
        """
        Initializes a quantum circuit.

        Args:
            qubits (List[int]): A list of qubit indices that this circuit acts upon.
            gates (List[Gate]): A list of Gate objects that make up the circuit.
        """
        self.qubits = qubits
        self.gates = gates

    def __repr__(self) -> str:
        """
        Returns a string representation of the circuit.
        """
        return f"QuantumCircuit(qubits={self.qubits}, num_gates={len(self.gates)})"