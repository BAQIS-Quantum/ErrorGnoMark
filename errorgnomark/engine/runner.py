# errorgnomark/engine/runner.py
from typing import List, Dict, Any
from ..circuits.circuit import QuantumCircuit
# [MODIFICATION 1]: Instead of importing a concrete DummyBackend, import the abstract BaseBackend
from ..backends.base_backend import BaseBackend
from ..experiments.base_experiment import BaseExperiment 

class Runner:
    """
    The experiment executor.
    
    It takes an experiment definition and a backend, and is responsible for 
    executing the workflow.
    """
    # [MODIFICATION 2]: Changed the type hint in the __init__ method from DummyBackend to BaseBackend
    def __init__(self, backend: BaseBackend):
        """
        Initializes the Runner.

        Args:
            backend: An object that adheres to the BaseBackend interface, used for 
                     executing circuits.
        """
        # This check is now more generic and robust.
        if not hasattr(backend, 'run'):
            raise TypeError("The provided backend object must have a 'run' method.")
        self.backend = backend

    def run(self, experiment: BaseExperiment, shots: int) -> List[Dict[str, Any]]:
        """
        Runs a complete experiment.

        Args:
            experiment: An experiment object, e.g., XEBExperiment, which must have
                        a `generate_circuits` method.
            shots: The number of times each circuit should be run.

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
            print(f"  - Running circuit {i+1}/{len(circuits)} for {shots} shots...")
            
            result = self.backend.run(circuit, shots=shots)
            results.append(result)
        
        print("Runner: Experiment execution finished.")
        return results