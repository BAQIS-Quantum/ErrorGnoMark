# File Path: errorgnomark/engine.py
# REVISED: Added a batch execution method 'execute'.

from typing import TYPE_CHECKING, List, Tuple, Dict

if TYPE_CHECKING:
    from errorgnomark.backends.base_backend import BaseBackend
    from errorgnomark.circuits.circuit import QuantumCircuit


class QuantumEngine:
    """
    The QuantumEngine orchestrates the execution of quantum circuits on a specified backend.
    """

    def __init__(self, backend: 'BaseBackend'):
        """
        Initializes the QuantumEngine with a specific backend.
        """
        from errorgnomark.backends.base_backend import BaseBackend
        
        if not isinstance(backend, BaseBackend):
            raise TypeError(
                f"The provided backend must be a subclass of BaseBackend, "
                f"but got type {type(backend).__name__}."
            )
        
        self.backend = backend
        # This print statement is removed from here to avoid redundancy when using execute.

    def run(self, circuit: 'QuantumCircuit', shots: int = 1024) -> Tuple[Dict[str, float], Dict[str, int]]:
        """
        Runs a SINGLE quantum circuit on the configured backend.

        Args:
            circuit: The QuantumCircuit object to be executed.
            shots: The number of measurement shots to perform.

        Returns:
            The results from the backend's run method.
        """
        return self.backend.run(circuit, shots)

    # --- 新增方法: 添加批量执行功能 ---
    def execute(
        self, 
        circuits: List['QuantumCircuit'], 
        shots: int = 1024
    ) -> List[Tuple[Dict[str, float], Dict[str, int]]]:
        """
        Executes a BATCH of quantum circuits on the configured backend.

        This method iterates through a list of circuits and runs each one,
        collecting the results.

        Args:
            circuits: A list of QuantumCircuit objects to be executed.
            shots: The number of shots to use for EACH circuit in the batch.

        Returns:
            A list of results, where each result corresponds to a circuit
            in the input list.
        """
        print(
            f"Engine is executing a batch of {len(circuits)} circuits "
            f"on {self.backend.__class__.__name__} ({shots} shots each)..."
        )
        
        results = []
        for i, circuit in enumerate(circuits):
            # Optional: Add progress tracking for large batches
            # print(f"  Running circuit {i+1}/{len(circuits)}...")
            result = self.run(circuit, shots)
            results.append(result)
            
        print("Batch execution complete.")
        return results