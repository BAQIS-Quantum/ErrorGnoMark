# errorgnomark/experiments/characterization/spam/spam_characterization.py

from typing import List

# Use a forward reference for type hinting to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from errorgnomark.backends.base_backend import BaseBackend

# Import the existing, minimal BaseExperiment class
from errorgnomark.experiments.base_experiment import BaseExperiment
from errorgnomark.circuits.circuit import QuantumCircuit, Gate

# SPAMCharacterization inherits from the minimal BaseExperiment
class SPAMCharacterization(BaseExperiment):
    """
    An experiment to characterize State Preparation and Measurement (SPAM) errors.

    This experiment generates two simple circuits:
    1. Prepare |0> and measure.
    2. Prepare |1> (using an X gate) and measure.

    Analysis of the results yields the SPAM confusion matrix.
    """
    def __init__(self, qubits: List[int], backend: 'BaseBackend'):
        """
        Initializes the SPAM characterization experiment.

        Args:
            qubits: The list of qubits to characterize. Currently supports one qubit.
            backend: The backend on which the experiment will be run.
        """
        if len(qubits) != 1:
            raise ValueError("SPAMCharacterization currently supports only a single qubit.")
        
        self.qubits = qubits
        self.backend = backend
        self._circuits = self._create_circuits()

    def _create_circuits(self) -> List[QuantumCircuit]:
        """
        Generates the circuits needed for SPAM characterization.
        
        Returns:
            A list containing two circuits: one for |0> and one for |1>.
        """
        circuits = []
        target_qubit = self.qubits[0]

        # Circuit 1: Prepare |0>, Measure.
        circ_0 = QuantumCircuit(qubits=[target_qubit], gates=[])
        circ_0.metadata = {
            'name': f"spam_prep0_q{target_qubit}",
            'experiment_type': 'spam',
            'qubits': self.qubits,
            'ideal_state': '0'  # This tells the analysis function what was prepared.
        }
        # --- DEBUGGING LINE: This will prove the new code is running. ---
        print(f"  - [DEBUG] Created circuit with metadata: {circ_0.metadata}")
        circuits.append(circ_0)

        # Circuit 2: Prepare |1>, Measure.
        circ_1 = QuantumCircuit(
            qubits=[target_qubit],
            gates=[Gate(name='X', qubits=[target_qubit])]
        )
        circ_1.metadata = {
            'name': f"spam_prep1_q{target_qubit}",
            'experiment_type': 'spam',
            'qubits': self.qubits,
            'ideal_state': '1'  # This tells the analysis function what was prepared.
        }
        # --- DEBUGGING LINE: This will prove the new code is running. ---
        print(f"  - [DEBUG] Created circuit with metadata: {circ_1.metadata}")
        circuits.append(circ_1)

        return circuits

    def generate_circuits(self) -> List[QuantumCircuit]:
        """
        Public method to retrieve the circuits for this experiment.
        This is the interface expected by the Runner.
        
        Returns:
            A list of QuantumCircuit objects generated for the experiment.
        """
        return self._circuits