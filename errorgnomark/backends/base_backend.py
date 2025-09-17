# errorgnomark/backends/base_backend.py 

import abc
from typing import Dict, Tuple

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

        This method must be implemented by all concrete backend classes.

        Args:
            circuit: The QuantumCircuit object to execute.
            shots: The number of times to run the circuit to gather statistics.

        Returns:
            A tuple containing:
            - ideal_probabilities (Dict[str, float]): A dictionary mapping each
              output bitstring to its THEORETICAL, EXACT probability.
            - noisy_counts (Dict[str, int]): A dictionary mapping each
              output bitstring to the number of times it was measured in the
              noisy simulation/experiment.
        """
        pass