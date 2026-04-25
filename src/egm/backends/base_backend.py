# File Path: errorgnomark/backends/base_backend.py
# [DEFINITIVE FINAL VERSION - Use this to replace your current file]

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional

# --- Internal Framework Imports ---
try:
    from egm.circuits.circuit import QuantumCircuit
except ImportError:
    # Fallback for standalone execution or testing
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from egm.circuits.circuit import QuantumCircuit


class BaseBackend(ABC):
    """
    Abstract base class for all execution backends in the ErrorGnomark framework.

    This class defines the "contract" that all backends, whether they are
    simulators or interfaces to real hardware, must follow. The core of this
    contract is the `run` method.
    """
    
    def __init__(self, name: str):
        """
        Initializes the base backend.

        Args:
            name (str): The identifier for the backend (e.g., "DummyBackend", "IdealBackend").
        """
        self._name = name

    @property
    def name(self) -> str:
        """Returns the name of the backend."""
        return self._name

    @abstractmethod
    def run(self, 
            circuit: QuantumCircuit, 
            shots: Optional[int] = None
           ) -> Tuple[Any, Optional[Dict[str, int]]]:
        """
        Executes a single quantum circuit.

        This is the central method for any backend. It takes a circuit and an
        optional number of shots and returns the results.

        Args:
            circuit (QuantumCircuit): The circuit to be executed.
            shots (Optional[int]): The number of times the circuit is run and measured.
                                   This may be ignored by some backends (like ideal ones).

        Returns:
            A tuple containing:
            - result_obj (Any): A backend-specific result object. For simulators,
              this could be the final statevector. For hardware, it might be a
              job ID or None.
            - counts (Optional[Dict[str, int]]): A dictionary mapping measured bitstrings
              to the number of times they were observed. Can be None if not applicable.
        """
        pass
