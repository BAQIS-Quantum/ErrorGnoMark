# errorgnomark/engine/runner.py
from typing import List, Dict, Any, Type
from ..circuits.circuit import QuantumCircuit # Assuming base experiment class exists
from ..backends.dummy_backend import DummyBackend

class Runner:
    """
    The experiment executor.
    
    It takes an experiment definition and a backend, and is responsible for 
    executing the workflow.
    """
    def __init__(self, backend: DummyBackend):
        """
        Initializes the Runner.

        Args:
            backend: An object that adheres to the backend interface, used for 
                     executing circuits.
        """
        self.backend = backend
        print("Runner initialized.")

    def run(self, experiment: Any) -> List[Dict[str, Any]]:
        """
        Runs a complete experiment.

        Args:
            experiment: An experiment object, e.g., XEBExperiment, which must have
                        a `generate_circuits` method.

        Returns:
            A list where each element is the raw result of a single circuit run.
        """
        print(f"Runner: Starting experiment '{type(experiment).__name__}' on backend '{type(self.backend).__name__}'.")
        
        # 1. Generate all necessary circuits from the experiment definition
        circuits: List[QuantumCircuit] = experiment.generate_circuits()
        print(f"Runner: Generated {len(circuits)} circuits to run.")

        # 2. Execute each circuit on the backend and collect the results
        results = []
        for i, circuit in enumerate(circuits):
            print(f"  - Running circuit {i+1}/{len(circuits)}...")
            result = self.backend.run(circuit)
            results.append(result)
        
        print("Runner: Experiment execution finished.")
        return results