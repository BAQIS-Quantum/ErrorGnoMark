from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

# Assuming your circuit and base_experiment structures are in these paths
from ....base_experiment import BaseExperiment
from .....circuits.circuit import QuantumCircuit

class BaseStateTomographyExperiment(BaseExperiment, ABC):
    """
    Abstract base class for all state tomography experiments.

    This class defines the common interface and workflow for characterizing a quantum state
    prepared by a given circuit. Subclasses must implement the logic for generating
    the specific measurement circuits and processing the results.
    """
    def __init__(self, qubits: List[int], state_prep_circuit: QuantumCircuit):
        """
        Initializes the state tomography experiment.

        Args:
            qubits: A list of qubit indices involved in the experiment.
            state_prep_circuit: The QuantumCircuit object that prepares the target state.
        """
        # Assuming BaseExperiment has its own __init__
        super().__init__() 
        if not qubits:
            raise ValueError("Qubit list cannot be empty.")
        if not isinstance(state_prep_circuit, QuantumCircuit):
            raise TypeError("state_prep_circuit must be a QuantumCircuit object.")
            
        self.qubits = qubits
        self.state_prep_circuit = state_prep_circuit
        self._results = None
        self._density_matrix = None

    def run(self, backend: Any) -> Dict[str, Any]:
        """
        Executes the full tomography experiment on a given backend.

        This method orchestrates the entire process:
        1. Generates the necessary measurement circuits.
        2. Composes them with the state preparation circuit.
        3. Executes the combined circuits on the backend.
        4. Stores and returns the raw results.

        Args:
            backend: An object representing the quantum backend, which has a `run` method.

        Returns:
            A dictionary containing the raw measurement results from the backend.
        """
        print("Starting state tomography experiment...")
        
        # 1. Generate measurement circuits based on the specific tomography scheme
        measurement_circuits_map = self._create_measurement_circuits()
        print(f"Generated {len(measurement_circuits_map)} measurement bases.")

        # 2. Compose state preparation with each measurement circuit
        full_circuits_to_run = {}
        for basis, meas_circ in measurement_circuits_map.items():
            # The compose method should ideally be part of your QuantumCircuit class
            # For now, we assume it concatenates gates.
            combined_gates = self.state_prep_circuit.gates + meas_circ.gates
            full_circuit = QuantumCircuit(qubits=self.qubits, gates=combined_gates)
            full_circuits_to_run[basis] = full_circuit
        
        # 3. Execute on backend (this is where your `engine` would be used)
        print(f"Executing {len(full_circuits_to_run)} circuits on the backend...")
        # The backend's run method should accept a dictionary of circuits
        # and return a dictionary of results (e.g., counts).
        self._results = backend.run(full_circuits_to_run)
        print("Execution complete.")
        
        return self._results

    @abstractmethod
    def _create_measurement_circuits(self) -> Dict[str, QuantumCircuit]:
        """
        Abstract method to be implemented by subclasses.
        
        Should return a dictionary mapping a basis identifier (e.g., 'XX', 'YY')
        to a QuantumCircuit that performs the basis transformation.
        """
        pass

    @abstractmethod
    def analyze(self, **kwargs) -> Any:
        """
        Abstract method for data processing and analysis.
        
        This method should take the stored results and perform the state reconstruction
        and any other analysis. It will typically call classes from the `analysis` module.
        """
        pass