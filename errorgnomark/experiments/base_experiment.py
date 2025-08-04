# errorgnomark/experiments/base_experiment.py
from abc import ABC, abstractmethod
from typing import List
# Use a relative import to ensure correct module resolution within the package.
from ..circuits.circuit import QuantumCircuit

class BaseExperiment(ABC):
    """
    An abstract base class (ABC) for all experiment types.

    It defines the common interface (a "contract") that the Runner expects
    any experiment object to have.
    """
    @abstractmethod
    def generate_circuits(self) -> List[QuantumCircuit]:
        """
        Each concrete experiment class must implement this method to generate its
        list of quantum circuits. The Runner will call this method.
        
        Returns:
            A list of QuantumCircuit objects.
        """
        pass