# errorgnomark/experiments/entanglement_verification/bell_state.py

from typing import Any, Dict, List, Optional

from .base_entanglement import BaseEntanglementVerification
from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.circuits.circuit import Gate, QuantumCircuit

class BellStateVerification(BaseEntanglementVerification):
    """
    Experiment to verify the creation of a 2-qubit Bell state.

    This class prepares the Bell state |Φ+⟩ = (|00⟩ + |11⟩) / sqrt(2),
    measures it in the computational basis, and calculates the fidelity
    based on the probability of obtaining the |00⟩ and |11⟩ outcomes.
    """

    def __init__(
        self,
        qubits: List[int],
        backend: Optional[BaseBackend] = None,
        shots: int = 4096,
    ):
        """
        Initializes the Bell state verification experiment.

        Args:
            qubits: A list containing two qubit indices, e.g., [0, 1].
            backend: The backend to execute the circuit on.
            shots: The number of measurement shots.
        """
        super().__init__(qubits, backend, shots)
        if len(self.qubits) != 2:
            raise ValueError(f"Bell states require exactly 2 qubits, but {len(self.qubits)} were given.")

    def _generate_verification_circuit(self) -> QuantumCircuit:
        """
        Generates the circuit to create a Bell state |Φ+⟩.

        The circuit consists of:
        1. A Hadamard gate on the first qubit.
        2. A CNOT gate with the first qubit as control and the second as target.
        """
        q0, q1 = self.qubits
        gates = [
            Gate(name="H", target=q0),
            Gate(name="CNOT", control=q0, target=q1),
        ]
        # All qubits are measured at the end by default in the BaseBackend
        return QuantumCircuit(qubits=self.qubits, gates=gates)

    def _analyze_results(self, noisy_counts: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculates the fidelity of the prepared Bell state.

        Fidelity is defined as the summed probability of measuring the
        two ideal outcomes: '00' and '11'.
        """
        total_shots = sum(noisy_counts.values())
        if total_shots == 0:
            return {'fidelity': 0.0, 'ideal_outcomes': ['00', '11'], 'raw_counts': noisy_counts}

        # Get counts for the two correct outcomes
        count_00 = noisy_counts.get("00", 0)
        count_11 = noisy_counts.get("11", 0)

        fidelity = (count_00 + count_11) / total_shots

        return {
            'fidelity': fidelity,
            'ideal_outcomes': ['00', '11'],
            'raw_counts': noisy_counts,
        }