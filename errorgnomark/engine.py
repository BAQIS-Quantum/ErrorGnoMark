# File Path: errorgnomark/engine.py
# [DEFINITIVE FINAL VERSION v4 - Unified Smart Engine Architecture]

import logging
from typing import List, Tuple, Dict
import numpy as np

# --- Internal Framework Imports ---
try:
    from .circuits.circuit import QuantumCircuit
    from .backends.base_backend import BaseBackend
    from .backends.ideal_backend import IdealBackend
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from errorgnomark.circuits.circuit import QuantumCircuit
    from errorgnomark.backends.base_backend import BaseBackend
    from errorgnomark.backends.ideal_backend import IdealBackend

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

class QuantumEngine:
    """
    The QuantumEngine orchestrates the execution of quantum circuits. It follows a
    "Smart Engine" design, where the engine is responsible for coordinating both
    ideal simulations and noisy backend executions.
    """
    def __init__(self, backend: BaseBackend):
        """
        Initializes the QuantumEngine with a specific noisy backend.

        Args:
            backend: An instance of a class that inherits from BaseBackend.
                     This backend's `run` method is expected to return noisy counts.
        """
        if not isinstance(backend, BaseBackend):
            raise TypeError("Engine must be initialized with an object that inherits from BaseBackend.")
        
        self.backend = backend
        # The engine maintains its own internal, noise-free simulator to generate
        # ideal probability distributions for comparison.
        self.ideal_backend = IdealBackend()
        
        logging.info(f"QuantumEngine initialized with backend '{self.backend.name}' and is ready.")

    def get_ideal_statevector(self, circuit: QuantumCircuit) -> np.ndarray:
        """
        Computes the ideal, noise-free statevector for a given circuit using
        the internal ideal simulator.

        Args:
            circuit: The QuantumCircuit object to simulate.

        Returns:
            A numpy array representing the final statevector.
        """
        # The IdealBackend's run method returns (statevector, None)
        statevector, _ = self.ideal_backend.run(circuit)
        return statevector

    def _statevector_to_probs(self, statevector: np.ndarray, num_qubits: int) -> Dict[str, float]:
        """Utility function to convert a statevector to a probability dictionary."""
        probabilities = np.abs(statevector)**2
        # Filter out near-zero probabilities for a cleaner dictionary
        return {format(i, f'0{num_qubits}b'): prob for i, prob in enumerate(probabilities) if prob > 1e-12}

    def execute_with_ideal(
        self,
        circuits: List[QuantumCircuit],
        shots: int
    ) -> List[Tuple[Dict[str, float], Dict[str, int]]]:
        """
        Executes a list of circuits, returning both ideal probabilities and noisy counts for each.
        This is the single, unified execution method for all benchmarking experiments.

        Args:
            circuits: A list of QuantumCircuit objects to execute.
            shots: The number of times to run each circuit on the noisy backend.

        Returns:
            A list of tuples. Each tuple is `(ideal_probabilities, noisy_counts)`,
            corresponding to one input circuit.
        """
        num_circuits = len(circuits)
        logging.info(f"Executing {num_circuits} circuits with {shots} shots each on backend '{self.backend.name}'...")
        
        results = []
        for i, circuit in enumerate(circuits):
            if (i + 1) % 10 == 0 or i == num_circuits - 1:
                logging.info(f"  ... processing circuit {i+1}/{num_circuits}")
            
            # Step 1: Calculate the ideal probability distribution using the internal ideal simulator.
            # THIS IS THE CRITICAL FIX for the bug you discovered in the XEB plots.
            # It ensures each circuit is compared against its OWN ideal result.
            ideal_statevector = self.get_ideal_statevector(circuit)
            ideal_probabilities = self._statevector_to_probs(ideal_statevector, circuit.num_qubits)

            # Step 2: Run the circuit on the configured noisy backend to get measurement counts.
            # Our BaseBackend interface guarantees the run method returns a tuple,
            # and we only need the second element (the counts).
            _, noisy_counts = self.backend.run(circuit, shots=shots)
            
            # Step 3: Pair the results.
            results.append((ideal_probabilities, noisy_counts))

        logging.info("Execution complete.")
        return results
