# errorgnomark/backends/base_backend.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..circuits.circuit import QuantumCircuit

class BaseBackend(ABC):
    """
    Abstract Base Class for all execution backends.
    
    It defines the standard interface that every backend (e.g., simulators,
    real hardware providers) must implement.
    """
    @abstractmethod
    def run(self, circuit: QuantumCircuit, shots: int) -> Dict[str, Any]:
        """
        Executes a quantum circuit and returns the results.

        Args:
            circuit (QuantumCircuit): The circuit to be executed.
            shots (int): The number of times to run the circuit to gather statistics.

        Returns:
            Dict[str, Any]: A dictionary containing the measurement results.
                            The exact structure can vary between backends.
        """
        pass