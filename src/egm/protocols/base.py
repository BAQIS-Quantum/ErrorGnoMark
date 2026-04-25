# File Path: errorgnomark/experiments/base.py
# CORRECTED: Changed 'Engine' to 'QuantumEngine' to match the user's definition.

from abc import ABC, abstractmethod
from typing import List, Dict, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular imports if ExperimentResult needs Engine
if TYPE_CHECKING:
    from egm.core.circuits.circuit import QuantumCircuit
    from egm.core.backends.base_backend import BaseBackend
    from egm.analysis.result import ExperimentResult

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# [[[ FIX: Import the correct class name 'QuantumEngine' ]]]
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
from egm.execution.executor import QuantumEngine


class BaseExperiment(ABC):
    """
    Abstract Base Class for all characterization and benchmarking experiments.

    This class defines the standard interface that every experiment must implement,
    ensuring a consistent API across the library. An experiment is a self-contained
    "recipe" that knows how to generate its circuits and analyze its results.
    """

    def __init__(self, qubits: List[int]):
        """
        Initializes the experiment with the target qubits.
        
        Args:
            qubits: A list of qubit indices the experiment will run on.
        """
        self.qubits = qubits
        self.num_qubits = len(qubits)
        self._circuits: List['QuantumCircuit'] = []

    @abstractmethod
    def circuits(self) -> List['QuantumCircuit']:
        """
        Generates and returns all quantum circuits required for this experiment.

        This method encapsulates all circuit generation logic and should be
        deterministic if a seed is provided in the subclass's constructor.
        
        Returns:
            A list of QuantumCircuit objects.
        """
        raise NotImplementedError

    @abstractmethod
    def run(self, engine: QuantumEngine, **kwargs) -> Any:
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        # [[[ FIX: Update the type hint from 'Engine' to 'QuantumEngine' ]]]
        # Also removed backend from arguments as engine already contains it.
        # The return type is changed to 'Any' to be more flexible, as RB returns a Dict,
        # not necessarily a full ExperimentResult object.
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        """
        Executes the full end-to-end experiment.

        This method orchestrates the entire workflow:
        1. Generates circuits (by calling `self.circuits()`).
        2. Executes the circuits on a backend using the provided engine.
        3. Analyzes the results.
        4. Returns a structured result object (e.g., Dict or ExperimentResult).

        Args:
            engine: The execution engine responsible for backend communication.
            **kwargs: Experiment-specific options (e.g., `shots`).

        Returns:
            An object containing all relevant data and metadata from the experiment.
        """
        raise NotImplementedError