# errorgnomark/experiments/entanglement_verification/ghz_state.py

from typing import Any, Dict, List, Optional

from .base_entanglement import BaseEntanglementVerification
from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.circuits.circuit import Gate, QuantumCircuit

class GHZStateVerification(BaseEntanglementVerification):
    """
    Experiment to verify the creation of an N-qubit GHZ state.

    This class prepares the GHZ state = (|0...0⟩ + |1...1⟩) / sqrt(2),
    measures it in the computational basis, and calculates the fidelity
    based on the probability of obtaining the all-zeros and all-ones outcomes.
    """

    def __init__(
        self,
        qubits: List[int],
        backend: Optional[BaseBackend] = None,
        shots: int = 4096,
    ):
        """
        Initializes the GHZ state verification experiment.

        Args:
            qubits: A list of two or more qubit indices.
            backend: The backend to execute the circuit on.
            shots: The number of measurement shots.
        """
        super().__init__(qubits, backend, shots)
        if len(self.qubits) < 2:
            raise ValueError(f"GHZ states require at least 2 qubits, but {len(self.qubits)} were given.")

    def _generate_verification_circuit(self) -> QuantumCircuit:
        """
        Generates the circuit to create an N-qubit GHZ state.

        The circuit consists of:
        1. A Hadamard gate on the first qubit.
        2. A chain of CNOT gates from qubit `i` to `i+1` for all subsequent qubits.
        """
        gates = [Gate(name="H", target=self.qubits[0])]
        for i in range(len(self.qubits) - 1):
            control_qubit = self.qubits[i]
            target_qubit = self.qubits[i+1]
            gates.append(Gate(name="CNOT", control=control_qubit, target=target_qubit))

        return QuantumCircuit(qubits=self.qubits, gates=gates)

    def _analyze_results(self, noisy_counts: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculates the fidelity of the prepared GHZ state.

        Fidelity is defined as the summed probability of measuring the
        two ideal outcomes: the all-'0's state and the all-'1's state.
        """
        total_shots = sum(noisy_counts.values())
        if total_shots == 0:
            return {'fidelity': 0.0, 'ideal_outcomes': [], 'raw_counts': noisy_counts}

        n_qubits = len(self.qubits)
        state_all_zeros = "0" * n_qubits
        state_all_ones = "1" * n_qubits

        count_zeros = noisy_counts.get(state_all_zeros, 0)
        count_ones = noisy_counts.get(state_all_ones, 0)

        fidelity = (count_zeros + count_ones) / total_shots

        return {
            'fidelity': fidelity,
            'ideal_outcomes': [state_all_zeros, state_all_ones],
            'raw_counts': noisy_counts,
        }