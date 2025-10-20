# File Path: errorgnomark/backends/dummy_backend.py
# [DEFINITIVE FINAL VERSION v1.2 - Added Inheritance and Refactored Run Method]

import numpy as np
from typing import List, Dict, Optional, Tuple, Any

# --- Internal Framework Imports ---
try:
    from .base_backend import BaseBackend
    from ..circuits.circuit import QuantumCircuit
except ImportError:
    # Fallback for standalone execution or testing
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from errorgnomark.circuits.circuit import QuantumCircuit
    from errorgnomark.backends.base_backend import BaseBackend

# ==============================================================================
# === FIX: The DummyBackend class now inherits from BaseBackend ================
# ==============================================================================
class DummyBackend(BaseBackend):
    """
    A phenomenological backend for simulating Randomized Benchmarking experiments.

    This backend does not simulate the circuit statevector. Instead, it uses a
    statistical model to directly calculate the ground state survival probability
    based on the known fidelities of the operations.

    This class now inherits from BaseBackend and implements the required `run` method.
    """

    def __init__(
        self,
        clifford_fidelity: float = 0.99,
        gate_fidelities: Optional[Dict[str, float]] = None,
        spam_error_rate: float = 0.01,
        seed: Optional[int] = None
    ):
        """
        Initializes the phenomenological backend.

        Args:
            clifford_fidelity (float): The fidelity `p_C` of a single random Clifford gate.
            gate_fidelities (dict, optional): A dictionary mapping gate names (e.g., 'cz')
                                              to their fidelities `p_G`.
            spam_error_rate (float): The rate of SPAM error, used to define A and B.
            seed (int, optional): Seed for the random number generator for noise.
        """
        # === FIX: Call the parent class's constructor to register the backend name ===
        super().__init__(name="DummyBackend")
        
        self.clifford_fidelity = clifford_fidelity
        self.gate_fidelities = gate_fidelities if gate_fidelities is not None else {}
        self.spam_error_rate = spam_error_rate
        self.rng = np.random.default_rng(seed)

        # SPAM parameters
        self.A = 1.0 - spam_error_rate
        self.B = spam_error_rate

        print("DummyBackend initialized with a phenomenological model: ")
        print(f"  Clifford Fidelity p_C = {self.clifford_fidelity}")
        if self.gate_fidelities:
            print(f"  Gate Fidelities p_G = {self.gate_fidelities}")
        print(f"  SPAM Parameters: A={self.A:.3f}, B={self.B:.3f}")

    # ==============================================================================
    # === FIX: Implement the `run` method as required by BaseBackend contract ======
    # ==============================================================================
    def run(
        self,
        circuit: QuantumCircuit,
        shots: Optional[int] = 1000
    ) -> Tuple[Any, Optional[Dict[str, int]]]:
        """
        "Executes" a single circuit by generating outcome counts based on the model.
        This method fulfills the contract of the BaseBackend abstract class.

        Args:
            circuit (QuantumCircuit): The single circuit to run.
            shots (int): The number of shots for the circuit.

        Returns:
            A tuple (None, counts_dict), where counts_dict contains the simulated counts.
        """
        num_qubits = circuit.num_qubits
        depth = circuit.metadata.get('depth', 0)
        interleaved_gate_name = circuit.metadata.get('interleaved_gate_name')

        # Determine the decay parameter 'p' for this circuit
        if interleaved_gate_name:
            gate_fidelity = self.gate_fidelities.get(interleaved_gate_name)
            if gate_fidelity is None:
                raise ValueError(
                    f"DummyBackend does not have a fidelity defined for the "
                    f"interleaved gate '{interleaved_gate_name}'."
                )
            p = self.clifford_fidelity * gate_fidelity
        else:
            p = self.clifford_fidelity

        # Calculate the ideal survival probability from the RB decay formula
        ideal_survival_prob = self.A * (p ** depth) + self.B

        # Add binomial noise to simulate the finite number of shots
        num_success = self.rng.binomial(n=shots, p=ideal_survival_prob)

        ground_state_str = '0' * num_qubits
        # Use a representative excited state for non-ground state outcomes
        other_state_str = '1' * num_qubits

        counts = {
            ground_state_str: num_success,
            other_state_str: shots - num_success
        }
        
        # The BaseBackend contract expects a tuple: (result_object, counts)
        return (None, counts)

    def execute(
        self,
        circuits: List[QuantumCircuit],
        shots: int
    ) -> List[Tuple[None, Dict[str, int]]]:
        """
        Executes a list of circuits. This method is kept for backward compatibility
        with parts of the code that expect to pass a list of circuits. It now simply
        calls the main `run` method in a loop.

        Args:
            circuits (List[QuantumCircuit]): The list of circuits to run.
            shots (int): The number of shots for each circuit.

        Returns:
            A list of tuples, where each tuple is (None, counts_dict).
        """
        results = []
        for circuit in circuits:
            # Call the new, compliant `run` method for each circuit
            _, counts = self.run(circuit, shots=shots)
            results.append((None, counts))
        return results