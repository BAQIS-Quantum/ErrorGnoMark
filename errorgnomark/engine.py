# # File Path: errorgnomark/engine.py
# # [FINAL COMPATIBLE VERSION - Merges batch execution with ideal state simulation]

# from typing import List, Tuple, Dict
# import numpy as np

# # Use forward references for type hints to avoid circular imports
# from .circuits.circuit import QuantumCircuit
# from .backends.base_backend import BaseBackend

# class QuantumEngine:
#     """
#     The QuantumEngine orchestrates the execution of quantum circuits on a specified backend.
#     It supports both single circuit execution and batch execution.
#     """
#     def __init__(self, backend: BaseBackend):
#         if not isinstance(backend, BaseBackend):
#             raise TypeError(f"Backend must be a subclass of BaseBackend, but got {type(backend).__name__}.")
#         self.backend = backend
#         # The print statement is moved to the execute method for clarity on batch jobs.

#     def run(self, circuit: QuantumCircuit, shots: int = 1024) -> Tuple[Dict[str, float], Dict[str, int]]:
#         """
#         Runs a SINGLE quantum circuit on the configured backend.
#         """
#         return self.backend.run(circuit, shots)

#     def execute(self, circuits: List[QuantumCircuit], shots: int = 1024) -> List[Tuple[Dict[str, float], Dict[str, int]]]:
#         """
#         Executes a BATCH of quantum circuits on the configured backend.
#         """
#         print(f"Engine executing batch of {len(circuits)} circuits on {self.backend.__class__.__name__} ({shots} shots each)...")
        
#         # In a real-world scenario with a cloud backend, this would be a single API call.
#         # For our simulator, we loop.
#         results = [self.run(circuit, shots) for circuit in circuits]
            
#         print("Batch execution complete.")
#         return results

#     def get_ideal_statevector(self, circuit: QuantumCircuit) -> np.ndarray:
#         """
#         Simulates the circuit without noise to get the final ideal statevector.
#         This is a crucial helper for tomography and other characterization tasks.
#         """
#         if not hasattr(self.backend, '_simulate_statevector'):
#             raise NotImplementedError(f"The backend '{self.backend.__class__.__name__}' does not support ideal statevector simulation.")
        
#         # We call the backend's internal simulation method without applying any noise.
#         return self.backend._simulate_statevector(circuit, apply_coherent_errors=False)

# File Path: errorgnomark/engine.py
# [DEFINITIVE FINAL VERSION v3 - Compatible with new BaseBackend API]

from typing import List, Union, Dict
from .circuits.circuit import QuantumCircuit
from .backends.base_backend import BaseBackend

class QuantumEngine:
    """
    The central execution unit of the framework.

    It takes circuits from an Experiment, runs them on a Backend,
    and returns the results.
    """
    def __init__(self, backend: BaseBackend):
        if not isinstance(backend, BaseBackend):
            raise TypeError("Engine must be initialized with an object that inherits from BaseBackend.")
        self.backend = backend
        print("QuantumEngine initialized and ready.")

    def run(self, circuit: QuantumCircuit, shots: int) -> Dict[str, int]:
        """
        Runs a single quantum circuit and returns the measurement counts.

        This method acts as a wrapper around the backend's run method,
        extracting only the counts dictionary that most experiments need.
        """
        # The backend returns (probabilities, counts). We only need the counts here.
        _, counts = self.backend.run(circuit, shots)
        return counts

    def execute(self, circuits: Union[QuantumCircuit, List[QuantumCircuit]], shots: int) -> List[Dict[str, int]]:
        """
        Executes a batch of circuits.
        """
        if isinstance(circuits, QuantumCircuit):
            circuits = [circuits]
        
        print(f"Engine executing batch of {len(circuits)} circuits on {self.backend.__class__.__name__} ({shots} shots each)...")
        
        # The backend returns (probabilities, counts). We extract counts for each circuit.
        results = [self.backend.run(circuit, shots)[1] for circuit in circuits]
        
        print("Batch execution complete.")
        return results