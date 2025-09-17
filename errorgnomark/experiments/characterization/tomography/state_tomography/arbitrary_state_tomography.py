# File Path: errorgnomark/experiments/characterization/tomography/state_tomography/arbitrary_state_tomography.py
# This version makes the measurement_bases list public for easy access.

import itertools
from typing import List, Dict, Any

from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.experiments.base_experiment import BaseExperiment
from errorgnomark.analysis.characterization.state_tomography_analysis import StateTomographyAnalysis

class ArbitraryStateTomographyExperiment(BaseExperiment):
    """
    Performs state tomography on an arbitrary N-qubit state prepared by a given circuit.
    """
    def __init__(self, qubits: List[int], state_prep_circuit: QuantumCircuit):
        super().__init__()
        if not qubits:
            raise ValueError("Experiment must be initialized with at least one qubit.")
        
        self.qubits = qubits
        self.num_qubits = len(qubits)
        self.experiment_data: Dict[str, Any] = {}
        self.state_prep_circuit = state_prep_circuit
        
        # --- [MODIFICATION]: Renamed from _measurement_bases to make it public ---
        self.measurement_bases = self._generate_measurement_bases()
        self.analysis_tool = StateTomographyAnalysis(qubits)

    def _generate_measurement_bases(self) -> List[str]:
        """Generates all N-qubit Pauli measurement bases ('IXYZ' combinations)."""
        return ["".join(p) for p in itertools.product('IXYZ', repeat=self.num_qubits)]

    def _create_tomography_circuit(self, basis: str) -> QuantumCircuit:
        tomo_circuit = self.state_prep_circuit.copy()
        for i, pauli_op in enumerate(basis):
            qubit = self.qubits[i]
            if pauli_op == 'X':
                tomo_circuit.add_gate(Gate('h', (qubit,)))
            elif pauli_op == 'Y':
                tomo_circuit.add_gate(Gate('sdg', (qubit,)))
                tomo_circuit.add_gate(Gate('h', (qubit,)))
        return tomo_circuit

    def run(self, backend: BaseBackend, shots: int):
        print(f"Starting ArbitraryStateTomographyExperiment with {shots} shots per basis.")
        self.experiment_data = {"num_qubits": self.num_qubits}
        
        num_bases = len(self.measurement_bases)
        for i, basis in enumerate(self.measurement_bases, 1):
            print(f"Running circuit {i}/{num_bases} (Basis: {basis})...")
            circuit = self._create_tomography_circuit(basis)
            ideal_probs, counts = backend.run(circuit, shots=shots)
            
            total_counts = sum(counts.values())
            observed_probabilities = {outcome: count / total_counts for outcome, count in counts.items()} if total_counts > 0 else {}
            
            expectation = 0
            for outcome_str, prob in observed_probabilities.items():
                parity = sum(1 for j, pauli_char in enumerate(basis) if pauli_char != 'I' and outcome_str[j] == '1')
                sign = (-1)**parity
                expectation += sign * prob

            self.experiment_data[basis] = {
                'counts': counts,
                'probabilities': observed_probabilities,
                'ideal_probabilities': ideal_probs,
                'expectation': expectation
            }
        print("Experiment run completed. All measurement results collected.")