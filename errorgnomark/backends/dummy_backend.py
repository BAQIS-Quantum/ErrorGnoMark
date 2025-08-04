# errorgnomark/backends/dummy_backend.py
import random
from collections import Counter
from typing import Dict, Any

from .base_backend import BaseBackend
from ..circuits.circuit import QuantumCircuit

class DummyBackend(BaseBackend):
    """
    A simple simulator backend for testing and demonstration purposes.
    This backend uses a simplified, circuit-level noise model.
    """
    def __init__(self, depolarizing_error: float = 0.0):
        if not 0.0 <= depolarizing_error <= 1.0:
            raise ValueError("depolarizing_error must be between 0 and 1.")
        self.depolarizing_error = depolarizing_error
        print(f"DummyBackend initialized with depolarizing error = {self.depolarizing_error}")

    def run(self, circuit: QuantumCircuit, shots: int) -> Dict[str, Any]:
        """
        Simulates the execution of a quantum circuit for a specified number of shots.
        
        NOTE: This is a highly simplified noise model. It calculates an overall
        error probability based on the total number of gates and applies a
        potential bit-flip to a random qubit for each shot.
        """
        num_qubits = len(circuit.qubits)
        ideal_final_state = '0' * num_qubits
        ideal_counts = {ideal_final_state: shots}

        # --- [Change 1]: The source of error is now all gates, not just CNOTs ---
        # We calculate the total number of gates in the circuit.
        num_gates = len(circuit.gates)
        
        # The probability of "at least one error" is calculated based on the total number of gates.
        # Each gate has a probability of (1 - p) of being perfect.
        # The probability of the entire circuit being perfect is (1 - p)^num_gates.
        # Therefore, the probability of at least one error occurring is 1 - (1 - p)^num_gates.
        error_probability = 1 - (1 - self.depolarizing_error) ** num_gates

        noisy_counts = Counter()
        for _ in range(shots):
            # Simulate whether an error occurred in this particular shot
            if random.random() < error_probability:
                # If an error occurred, we will randomly select a qubit to flip.
                noisy_final_state = list(ideal_final_state)
                
                # --- [Change 2]: The error is applied randomly to any qubit ---
                qubit_to_flip = random.randint(0, num_qubits - 1)
                
                # Flip the selected bit
                if noisy_final_state[qubit_to_flip] == '0':
                    noisy_final_state[qubit_to_flip] = '1'
                else:
                    noisy_final_state[qubit_to_flip] = '0'
                
                noisy_counts[''.join(noisy_final_state)] += 1
            else:
                # If no error occurred, record the ideal result
                noisy_counts[ideal_final_state] += 1

        return {
            "ideal_counts": ideal_counts,
            "noisy_counts": dict(noisy_counts)
        }