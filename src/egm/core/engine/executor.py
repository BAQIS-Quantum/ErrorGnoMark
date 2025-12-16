# File: errorgnomark/engine/executor.py
# ---------------------------------------------------------------------
# Module: QuantumEngine — Circuit Execution Orchestrator
# ---------------------------------------------------------------------
# This module defines the QuantumEngine class, responsible for
# coordinating the execution of quantum circuits on both ideal and
# noisy backends within the ErrorGnoMark framework.
#
# Responsibilities:
#   • Manage interaction between experimental circuits and backends.
#   • Provide ideal reference execution using an internal simulator.
#   • Support backward-compatible `run()` method for legacy workflows.
#
# Version: 5 (Stable / Compatible)
# ---------------------------------------------------------------------

import logging
from typing import List, Tuple, Dict, Optional
import numpy as np

# ---------------------------------------------------------------------
# Internal Framework Imports
# ---------------------------------------------------------------------
try:
    from .circuits.circuit import QuantumCircuit
    from .backends.base_backend import BaseBackend
    from .backends.ideal_backend import IdealBackend
except ImportError:
    import sys
    import os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from egm.core.circuits.circuit import QuantumCircuit
    from egm.core.backends.base_backend import BaseBackend
    from egm.core.backends.ideal_backend import IdealBackend

# ---------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# ---------------------------------------------------------------------
# QuantumEngine Definition
# ---------------------------------------------------------------------
class QuantumEngine:
    """
    Engine responsible for orchestrating execution of quantum circuits.

    The QuantumEngine manages two execution paths:
      1. Ideal simulations (for reference probabilities)
      2. Noisy executions (on a provided backend)

    It supports both modern vectorized experiment workflows and legacy
    single-circuit execution through the backward-compatible `run()` method.
    """

    # -----------------------------------------------------------------
    # Initialization
    # -----------------------------------------------------------------
    def __init__(self, backend: BaseBackend):
        """
        Initialize the QuantumEngine with a given noisy backend.

        Args:
            backend: An instance of a backend implementing `BaseBackend`.
                     The backend's `run()` method must return `(statevector, counts)`.
        """
        if not isinstance(backend, BaseBackend):
            raise TypeError(
                "QuantumEngine must be initialized with a subclass of BaseBackend."
            )

        self.backend = backend
        self.ideal_backend = IdealBackend()  # Internal, noise-free simulator

        logging.info(
            f"QuantumEngine initialized with backend '{self.backend.name}' and ready for execution."
        )

    # -----------------------------------------------------------------
    # Backward Compatibility
    # -----------------------------------------------------------------
    def run(
        self, circuit: QuantumCircuit, shots: int
    ) -> Tuple[Optional[np.ndarray], Dict[str, int]]:
        """
        Execute a single circuit on the configured backend.

        This method is retained for backward compatibility with legacy
        experiment scripts that call `engine.run()` directly.

        Args:
            circuit: The circuit to execute.
            shots: Number of repetitions to perform.

        Returns:
            A tuple `(statevector, counts)` as defined by the backend interface.
        """
        logging.debug(
            f"Running single circuit (compatibility mode) on backend '{self.backend.name}'."
        )
        return self.backend.run(circuit, shots=shots)

    # -----------------------------------------------------------------
    # Ideal Simulation Utilities
    # -----------------------------------------------------------------
    def get_ideal_statevector(self, circuit: QuantumCircuit) -> np.ndarray:
        """
        Compute the ideal, noise-free statevector for a given circuit.

        Args:
            circuit: The QuantumCircuit object to simulate.

        Returns:
            Noise-free statevector of the circuit.
        """
        statevector, _ = self.ideal_backend.run(circuit)
        return statevector

    def _statevector_to_probs(
        self, statevector: np.ndarray, num_qubits: int
    ) -> Dict[str, float]:
        """
        Convert a statevector into a probability distribution over bitstrings.

        Args:
            statevector: Complex amplitude vector.
            num_qubits: Number of qubits in the circuit.

        Returns:
            Dictionary mapping bitstrings to probabilities.
        """
        probabilities = np.abs(statevector) ** 2
        return {
            format(i, f"0{num_qubits}b"): prob
            for i, prob in enumerate(probabilities)
            if prob > 1e-12
        }

    # -----------------------------------------------------------------
    # Primary Modern Execution
    # -----------------------------------------------------------------
    def execute_with_ideal(
        self, circuits: List[QuantumCircuit], shots: int
    ) -> List[Tuple[Dict[str, float], Dict[str, int]]]:
        """
        Execute circuits, returning both ideal probabilities and noisy counts.

        This method is the unified modern interface used by all RB and
        Tomography-style benchmarking experiments.

        Args:
            circuits: A list of compiled QuantumCircuit objects.
            shots: Number of repeated executions per circuit.

        Returns:
            List of tuples, each `(ideal_probabilities, noisy_counts)`
            corresponding to a circuit.
        """
        num_circuits = len(circuits)
        results: List[Tuple[Dict[str, float], Dict[str, int]]] = []

        logging.info(
            f"Executing {num_circuits} circuits with {shots} shots each "
            f"on backend '{self.backend.name}'..."
        )

        for i, circuit in enumerate(circuits):
            if (i + 1) % 10 == 0 or i == num_circuits - 1:
                logging.info(f"  Processing circuit {i + 1} / {num_circuits}")

            # --- Step 1: Compute ideal probability distribution ---
            ideal_statevector = self.get_ideal_statevector(circuit)
            ideal_probs = self._statevector_to_probs(
                ideal_statevector, circuit.num_qubits
            )

            # --- Step 2: Execute on configured noisy backend ---
            _, noisy_counts = self.backend.run(circuit, shots=shots)

            # --- Step 3: Store results pair ---
            results.append((ideal_probs, noisy_counts))

        logging.info("All circuit executions completed successfully.")
        return results