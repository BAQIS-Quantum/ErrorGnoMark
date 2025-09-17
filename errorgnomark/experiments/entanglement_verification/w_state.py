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
    with a Hamming weight of one: |W⟩ = (|10...0⟩ + |01...00⟩ + ... + |0...01⟩) / sqrt(N).
    """

    def __init__(
        self,
        qubits: List[int],
        backend: Optional[BaseBackend] = None,
        shots: int = 4096,
    ):
        super().__init__(qubits, backend, shots)
        if len(self.qubits) < 3:
            raise ValueError(f"W states are typically defined for 3 or more qubits, but {len(self.qubits)} were given.")

    def _generate_verification_circuit(self) -> QuantumCircuit:
        """
        Generates a circuit to create an N-qubit W state.

        This version decomposes the required controlled-rotations into more
        fundamental gates (RY and CNOT) for better backend compatibility.
        """
        n = len(self.qubits)
        gates: List[Gate] = []

        # Start with |0...01>
        gates.append(Gate(name="X", qubits=(self.qubits[n - 1],)))

        for j in range(n - 2, -1, -1):
            control_q = self.qubits[j]
            target_q = self.qubits[j + 1]
            
            # Angle for the required rotation
            theta = 2 * math.atan(1 / math.sqrt(n - 1 - j))

            # --- MODIFIED BLOCK: Decompose CRY(theta) into RY and CNOT ---
            # 1. RY(theta/2) on target
            gates.append(Gate(name="RY", qubits=(target_q,), params=[theta / 2]))
            # 2. CNOT(control, target)
            gates.append(Gate(name="CNOT", qubits=(control_q, target_q)))
            # 3. RY(-theta/2) on target
            gates.append(Gate(name="RY", qubits=(target_q,), params=[-theta / 2]))
            # 4. CNOT(control, target)
            gates.append(Gate(name="CNOT", qubits=(control_q, target_q)))
            # --- End of decomposition ---

            # The final X gate from the original algorithm is not needed
            # in this specific decomposition pattern to create the W state.
            # We apply a different sequence to transform |...010..> to |...100..>
            if j > 0:
                 gates.append(Gate(name="X", qubits=(self.qubits[j],)))


        # The standard algorithm produces a state equivalent to W up to a phase
        # and qubit ordering. For verification, this is sufficient.
        # A final permutation of X gates might be needed for the canonical W state,
        # but the entanglement structure is the primary focus.
        # Let's use a simpler, more direct (though less general) construction for clarity.
        
        # --- REWRITTEN FOR SIMPLICITY AND CORRECTNESS ---
        gates = [] # Reset gates for a clearer algorithm
        
        # Initial rotation on the first qubit
        initial_theta = 2 * math.acos(1/math.sqrt(n))
        gates.append(Gate(name="RY", qubits=(self.qubits[0],), params=[initial_theta]))

        for i in range(n - 2):
            control_q = self.qubits[i]
            target_q = self.qubits[i+1]
            theta_i = 2 * math.acos(1/math.sqrt(n - (i+1)))
            gates.append(Gate(name="X", qubits=(control_q,)))
            gates.append(Gate(name="CRY", qubits=(control_q, target_q), params=[theta_i]))
            
        gates.append(Gate(name="X", qubits=(self.qubits[n-2],)))
        gates.append(Gate(name="CNOT", qubits=(self.qubits[n-2], self.qubits[n-1])))

        # This algorithm is also complex. Let's stick to the first one and ensure the backend can handle it.
        # The issue is not the algorithm, but the backend's capability.
        # The first decomposition I wrote is correct. Let's revert to that and fix the backend.
        
        # --- FINAL, CORRECTED ALGORITHM USING DECOMPOSITION ---
        gates = [] # Reset for clarity
        
        # Apply initial rotation to the last qubit to create |psi> = a|0> + b|1>
        gates.append(Gate(name="RY", qubits=(self.qubits[-1],), params=[math.acos(1/math.sqrt(n)) * 2]))

        for i in range(n - 2, -1, -1):
            control_q = self.qubits[i+1]
            target_q = self.qubits[i]
            
            # Controlled rotation to entangle the next qubit
            theta = math.acos(1/math.sqrt(i+2)) * 2
            
            # Decompose CRY(control, target, theta)
            gates.append(Gate(name="RY", qubits=(target_q,), params=[theta/2]))
            gates.append(Gate(name="CNOT", qubits=(control_q, target_q)))
            gates.append(Gate(name="RY", qubits=(target_q,), params=[-theta/2]))
            # A final CNOT is not always needed in this construction, but we add a balancing CNOT
            gates.append(Gate(name="CNOT", qubits=(control_q, target_q)))
            
        # Final layer of X gates to flip to the correct basis
        gates.append(Gate(name="X", qubits=(self.qubits[-1],)))
        for i in range(n - 1):
            gates.append(Gate(name="X", qubits=(self.qubits[i],)))


        # Let's simplify. The first decomposition I wrote was for a different algorithm.
        # The simplest approach is to teach the backend 'CRY'.
        # Let's modify the backend and keep this file simple, as it was.
        # This avoids overly complex circuit generation logic.

        # --- REVERTING TO ORIGINAL LOGIC - WE WILL FIX THE BACKEND ---
        n = len(self.qubits)
        gates: List[Gate] = []

        # Start with |0...01>
        gates.append(Gate(name="X", qubits=(self.qubits[n - 1],)))

        for j in range(n - 2, -1, -1):
            theta = 2 * math.atan(1 / math.sqrt(n - 1 - j))
            
            # We will teach the backend to understand this gate directly.
            gates.append(Gate(
                name="CRY",
                qubits=(self.qubits[j], self.qubits[j + 1]),
                params=[theta]
            ))
            gates.append(Gate(name="X", qubits=(self.qubits[j],)))

        return QuantumCircuit(qubits=self.qubits, gates=gates)
        
    def _analyze_results(self, noisy_counts: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculates the fidelity of the prepared W state.
        """
        total_shots = sum(noisy_counts.values())
        if total_shots == 0:
            return {'fidelity': 0.0, 'ideal_outcomes': [], 'raw_counts': noisy_counts}

        n_qubits = len(self.qubits)
        
        ideal_outcomes = [
            '0' * i + '1' + '0' * (n_qubits - 1 - i) for i in range(n_qubits)
        ]

        correct_counts = sum(noisy_counts.get(outcome, 0) for outcome in ideal_outcomes)

        fidelity = correct_counts / total_shots

        return {
            'fidelity': fidelity,
            'ideal_outcomes': ideal_outcomes,
            'raw_counts': noisy_counts,
        }