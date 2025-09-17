# errorgnomark/analysis/benchmarking/entanglement_verification/base_entanglement.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.circuits.circuit import QuantumCircuit

class BaseEntanglementVerification(ABC):
    # ... __init__ and other methods remain the same ...
    def __init__(
        self,
        qubits: List[int],
        backend: Optional[BaseBackend] = None,
        shots: int = 4096,
    ):
        self.qubits = sorted(qubits)
        self.backend = backend
        self.shots = shots
        self._last_circuit: Optional[QuantumCircuit] = None

    def print_last_circuit(self):
        """
        Prints a textual representation of the last generated quantum circuit.
        [MODIFIED] This version correctly renders multi-qubit gates.
        """
        if self._last_circuit is None:
            print("No circuit has been generated yet. Run the experiment first.")
            return

        circuit = self._last_circuit
        qubits = sorted(circuit.qubits)
        num_qubits = len(qubits)
        
        # Initialize the diagram as a list of lists of strings
        diagram = [['---' for _ in range(len(circuit.gates) + 1)] for _ in range(num_qubits)]
        qubit_map = {q: i for i, q in enumerate(qubits)}

        # Populate the diagram gate by gate
        for i, gate in enumerate(circuit.gates):
            gate_label = f"[{gate.name}]"
            
            if len(gate.qubits) == 1:
                q_idx = qubit_map[gate.qubits[0]]
                diagram[q_idx][i] = diagram[q_idx][i][:1] + gate_label + diagram[q_idx][i][1:]
            elif len(gate.qubits) == 2:
                control_q, target_q = gate.qubits
                control_idx = qubit_map[control_q]
                target_idx = qubit_map[target_q]
                
                # Place control and target symbols
                diagram[control_idx][i] = diagram[control_idx][i][:1] + '-●-' + diagram[control_idx][i][1:]
                diagram[target_idx][i] = diagram[target_idx][i][:1] + gate_label + diagram[target_idx][i][1:]
                
                # Draw the vertical line
                for r in range(min(control_idx, target_idx) + 1, max(control_idx, target_idx)):
                    diagram[r][i] = diagram[r][i][:2] + '|' + diagram[r][i][3:]

        # Print the diagram
        print(f"\n--- Circuit Diagram for {self.__class__.__name__} on Qubits {self.qubits} ---")
        for i, q in enumerate(qubits):
            line = f"q{q}: " + "".join(diagram[i])
            print(line.replace('-----', '---').replace('----', '---'))
        print("--- End of Diagram ---")

    # ... other abstract and concrete methods ...
    @abstractmethod
    def _generate_verification_circuit(self) -> QuantumCircuit:
        pass

    @abstractmethod
    def _analyze_results(self, noisy_counts: Dict[str, int]) -> Dict[str, Any]:
        pass

    def run(self, backend: Optional[BaseBackend] = None, shots: Optional[int] = None) -> Dict[str, Any]:
        effective_backend = backend or self.backend
        if effective_backend is None:
            raise ValueError("A backend must be provided either during initialization or in the run method.")
        
        effective_shots = shots or self.shots
        if effective_shots <= 0:
            raise ValueError("Number of shots must be positive.")

        circuit = self._generate_verification_circuit()
        self._last_circuit = circuit
        
        _, noisy_counts = effective_backend.run(circuit, shots=effective_shots)
        
        analysis = self._analyze_results(noisy_counts)
        return analysis