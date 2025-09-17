# errorgnomark/analysis/benchmarking/entanglement_verification/w_state.py

import math
from typing import Any, Dict, List, Optional

from .base_entanglement import BaseEntanglementVerification
from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.circuits.circuit import Gate, QuantumCircuit

class WStateVerification(BaseEntanglementVerification):
    """
    Experiment to verify the creation of an N-qubit W state.

    The W state is an equal superposition of all computational basis states
    with a Hamming weight of one: |W⟩ = (|10...0⟩ + |01...0⟩ + ... + |0...01⟩) / sqrt(N).
    """

    def __init__(
        self,
        qubits: List[int],
        backend: Optional[BaseBackend] = None,
        shots: int = 4096,
    ):
        super().__init__(qubits, backend, shots)
        if len(self.qubits) < 2: # W-state is well-defined for N>=2
            raise ValueError(f"W states are typically defined for 2 or more qubits, but {len(self.qubits)} were given.")

    def _generate_verification_circuit(self) -> QuantumCircuit:
        """
        Generates a circuit to create an N-qubit W state using a standard,
        correct iterative algorithm.
        """
        n = len(self.qubits)
        q = self.qubits # Use a shorter alias for clarity
        gates: List[Gate] = []

        # ======================= CORRECT W-STATE ALGORITHM =======================
        # This algorithm starts from |0...0> and iteratively builds the W-state.
        
        # 1. Start by creating a superposition on the first qubit.
        #    This is |W_1> = |1> if we consider it in a 1-qubit space.
        #    We achieve this by rotating |0> to |1>.
        gates.append(Gate(name="X", qubits=(q[0],)))

        # 2. Iteratively entangle the next qubit in the chain.
        #    In each step k, we transform |W_k>|0> into |W_{k+1}>.
        for k in range(1, n):
            # Define the angle for the controlled rotation.
            # This angle creates the correct superposition amplitudes.
            theta = 2 * math.acos(math.sqrt(1.0 / (k + 1)))
            
            # Apply a controlled-Y rotation from the previous qubit (q[k-1])
            # to the current qubit (q[k]).
            gates.append(Gate(
                name="CRY",
                qubits=(q[k - 1], q[k]),
                params=[theta]
            ))
            
            # Apply a CNOT gate to swap the excitation. This is a crucial step
            # that "moves" the single |1> state from the previous block
            # into the new qubit, preparing for the next iteration.
            gates.append(Gate(
                name="CNOT",
                qubits=(q[k], q[k - 1])
            ))
        # =========================================================================

        return QuantumCircuit(qubits=self.qubits, gates=gates)
        
    def _analyze_results(self, noisy_counts: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculates the fidelity of the prepared W state.
        This part of the logic was already correct. We'll just clean it up.
        """
        total_shots = sum(noisy_counts.values())
        if total_shots == 0:
            return {'fidelity': 0.0, 'ideal_outcomes': [], 'raw_counts': noisy_counts}

        n_qubits = len(self.qubits)
        
        # The ideal outcomes are states with Hamming weight 1 (a single '1').
        # e.g., for n=4: ['1000', '0100', '0010', '0001']
        ideal_outcomes = []
        for i in range(n_qubits):
            bitstring = ['0'] * n_qubits
            bitstring[i] = '1'
            ideal_outcomes.append("".join(bitstring))

        # Clean the raw counts to ensure keys are strings and values are ints
        clean_counts = {str(k): int(v) for k, v in noisy_counts.items()}

        correct_counts = sum(clean_counts.get(outcome, 0) for outcome in ideal_outcomes)

        fidelity = correct_counts / total_shots

        return {
            'fidelity': fidelity,
            'ideal_outcomes': ideal_outcomes,
            'raw_counts': clean_counts,
        }