# File Path: errorgnomark/backends/ideal_backend.py
# [NEW FILE - This file was missing]

from typing import Tuple, Dict, Optional
import numpy as np

# --- Internal Framework Imports ---
try:
    from .base_backend import BaseBackend
    from ..circuits.circuit import QuantumCircuit
    from ..simulators.statevector_simulator import StatevectorSimulator
except ImportError:
    # Fallback for standalone execution or testing
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from egm.core.backends.base_backend import BaseBackend
    from egm.core.circuits.circuit import QuantumCircuit
    from egm.core.backends.simulators.statevector_simulator import StatevectorSimulator


class IdealBackend(BaseBackend):
    """
    A backend that represents a perfect, noise-free statevector simulator.
    
    This class acts as a wrapper around the StatevectorSimulator to make it
    conform to the BaseBackend interface. Its `run` method returns the final
    statevector and `None` for counts, as there are no "shots" in an ideal
    simulation.
    """
    def __init__(self):
        """Initializes the IdealBackend."""
        # The name property is required by the BaseBackend interface.
        super().__init__(name="IdealBackend")
        self._simulator = StatevectorSimulator()

    def run(self, 
            circuit: QuantumCircuit, 
            shots: Optional[int] = None
           ) -> Tuple[np.ndarray, None]:
        """
        Performs a noise-free simulation of the circuit.

        Args:
            circuit: The QuantumCircuit to simulate.
            shots: This argument is ignored by the ideal backend but is kept
                   for interface compatibility.

        Returns:
            A tuple containing:
            - The final statevector (np.ndarray).
            - None (since there are no measurement counts).
        """
        # Use the internal statevector simulator to get the final state.
        final_statevector = self._simulator.run(circuit)
        
        # Return the result in the format required by the BaseBackend interface:
        # (result_object, counts_dict)
        return (final_statevector, None)
