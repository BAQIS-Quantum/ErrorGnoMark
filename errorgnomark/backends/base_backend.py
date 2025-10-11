# File Path: errorgnomark/backends/base_backend.py
# REVISED & CORRECTED VERSION

import abc
from typing import Dict, Tuple

# This try/except block is good practice for internal development
try:
    from errorgnomark.circuits.circuit import QuantumCircuit
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from errorgnomark.circuits.circuit import QuantumCircuit


class BaseBackend(abc.ABC):
    """
    Abstract base class for all quantum backends.

    A backend is responsible for executing a quantum circuit and returning
    the results of the simulation or experiment.
    """

    @abc.abstractmethod
    def run(self, circuit: QuantumCircuit, shots: int) -> Tuple[Dict[str, float], Dict[str, int]]:
        """
        Executes the given quantum circuit.

        This method simulates the circuit and returns the final probability
        distribution and the measurement counts from sampling.

        Args:
            circuit: The QuantumCircuit object to execute.
            shots: The number of times to sample from the final state to gather statistics.

        Returns:
            A tuple containing:
            - final_probabilities (Dict[str, float]): A dictionary mapping each
              output bitstring to its final probability after simulation. For a noisy
              backend, this includes noise effects. For an ideal backend, this is
              the ideal probability.
            - final_counts (Dict[str, int]): A dictionary mapping each
              output bitstring to the number of times it was measured, obtained by
              sampling `shots` times from the `final_probabilities`.
        """
        pass