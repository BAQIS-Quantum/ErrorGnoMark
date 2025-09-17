# errorgnomark/analysis/benchmarking/entanglement_verification/base_entanglement.py

import abc
from typing import Any, Dict, List, Optional, Tuple

# Note: The import path for BaseExperiment is absolute and remains correct.
from errorgnomark.experiments.base_experiment import BaseExperiment
from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.circuits.circuit import QuantumCircuit
from errorgnomark.circuits.visualization import format_circuit_as_string

class BaseEntanglementVerification(BaseExperiment, abc.ABC):
    """
    Abstract Base Class for Entanglement Verification Experiments.

    This class defines the standard interface for all entanglement verification
    tasks. It handles the common workflow of generating a circuit, executing it
    on a backend, and analyzing the results to compute a fidelity score.

    Subclasses must implement the following methods:
    - _generate_verification_circuit(): To create the specific quantum circuit
      that prepares the desired entangled state.
    - _analyze_results(): To calculate the state fidelity based on the
      measurement outcomes from the backend.
    """

    def __init__(
        self,
        qubits: List[int],
        backend: Optional[BaseBackend] = None,
        shots: int = 4096,
    ):
        """
        Initializes the entanglement verification experiment.

        Args:
            qubits: A list of qubit indices to be used for the state preparation.
            backend: The backend to execute the circuit on. Can be provided
                     here or in the `run` method.
            shots: The number of times to run the circuit for sampling.
        """
        super().__init__()
        self._validate_qubits(qubits)
        self.qubits = qubits
        self.backend = backend
        self.shots = shots
        self.last_circuit: Optional[QuantumCircuit] = None
        self.last_result: Optional[Dict[str, Any]] = None

    @staticmethod
    def _validate_qubits(qubits: Any):
        """Helper to validate the qubit list format."""
        if not isinstance(qubits, list) or not all(isinstance(q, int) for q in qubits):
            raise TypeError("`qubits` must be a list of integers.")

    @abc.abstractmethod
    def _generate_verification_circuit(self) -> QuantumCircuit:
        """
        Generates the quantum circuit to prepare and measure the entangled state.
        """
        pass

    @abc.abstractmethod
    def _analyze_results(self, noisy_counts: Dict[str, int]) -> Dict[str, Any]:
        """
        Analyzes the measurement counts to calculate state fidelity.
        """
        pass

    def run(
        self,
        backend: Optional[BaseBackend] = None,
        shots: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Runs the full verification experiment.
        """
        effective_backend = backend if backend is not None else self.backend
        if effective_backend is None:
            raise ValueError("A backend must be provided either at initialization or in `run()`.")

        effective_shots = shots if shots is not None else self.shots

        circuit = self._generate_verification_circuit()
        self.last_circuit = circuit

        _, noisy_counts = effective_backend.run(circuit, shots=effective_shots)

        result = self._analyze_results(noisy_counts)
        self.last_result = result

        return result

    def print_last_circuit(self):
        """Prints a string representation of the last executed circuit."""
        print(f"\n--- Circuit Diagram for {self.__class__.__name__} on Qubits {self.qubits} ---")
        if self.last_circuit is None:
            print("No circuit has been run yet. Call the `run()` method first.")
            return
        circuit_diagram = format_circuit_as_string(self.last_circuit)
        print(circuit_diagram)
        print("--- End of Diagram ---")