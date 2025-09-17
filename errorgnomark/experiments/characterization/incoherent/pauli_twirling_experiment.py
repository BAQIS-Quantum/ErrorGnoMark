# File Path: errorgnomark/experiments/characterization/incoherent/pauli_twirling_experiment.py
# FINAL FIX: Correctly unpacks the tuple returned by the DummyBackend.

from typing import List, Dict, Any, Tuple

from errorgnomark.experiments.base_experiment import BaseExperiment
from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.analysis.characterization.incoherent_analysis import analyze_pauli_twirling

class PauliTwirlingExperiment(BaseExperiment):
    """
    An experiment to characterize the depolarizing error of a single-qubit gate
    using the Pauli Twirling protocol.
    """
    def __init__(self, backend: 'BaseBackend', gate_name: str, qubits: List[int]):
        self.backend = backend
        if len(qubits) != 1:
            raise ValueError("Pauli Twirling experiment currently supports only single-qubit gates.")
        self.gate_name = gate_name
        self.qubits = qubits
        self._name = "PauliTwirlingExperiment"
        self._conjugation_map = {'H': {'I': 'I', 'X': 'Z', 'Y': 'Y', 'Z': 'X'}}
        self._inverse_map = {'H': 'H'}
        if self.gate_name not in self._conjugation_map:
            raise NotImplementedError(f"Pauli Twirling for gate '{self.gate_name}' is not implemented.")

    def generate_circuits(self) -> List[QuantumCircuit]:
        circuits = []
        paulis = ['I', 'X', 'Y', 'Z']
        target_qubit = self.qubits[0]
        gate_conjugation = self._conjugation_map[self.gate_name]
        gate_inverse = self._inverse_map[self.gate_name]

        for p_i_name in paulis:
            gate_list = []
            if p_i_name != 'I':
                gate_list.append(Gate(name=p_i_name, qubits=(target_qubit,)))
            gate_list.append(Gate(name=self.gate_name, qubits=(target_qubit,)))
            p_k_name = gate_conjugation[p_i_name]
            if p_k_name != 'I':
                gate_list.append(Gate(name=p_k_name, qubits=(target_qubit,)))
            gate_list.append(Gate(name=gate_inverse, qubits=(target_qubit,)))
            
            qc = QuantumCircuit(qubits=[target_qubit], gates=gate_list)
            qc.metadata = {'expected_outcome': '0', 'p_i': p_i_name, 'gate_name': self.gate_name}
            circuits.append(qc)
            
        return circuits

    def analyze(self, backend_results: List[Any]) -> Dict[str, Any]:
        """
        Analyzes the results of the Pauli Twirling experiment.
        It adapts the raw backend results to the format expected by the analysis function.
        """
        print("  > Analyzing Pauli Twirling results...")

        circuits_with_metadata = self.generate_circuits()

        if len(backend_results) != len(circuits_with_metadata):
            raise ValueError(f"Mismatch between number of results ({len(backend_results)}) "
                             f"and number of generated circuits ({len(circuits_with_metadata)}).")

        reconstructed_results = []
        for i, circuit in enumerate(circuits_with_metadata):
            metadata = circuit.metadata
            
            # --- THIS IS THE KEY FIX ---
            # The DummyBackend returns a tuple: (probabilities, counts).
            # We need to extract the second element, which is the counts dictionary.
            backend_result_tuple = backend_results[i]
            counts_dict = backend_result_tuple[1] # Unpack the tuple
            
            reconstructed_results.append((metadata, counts_dict))

        return analyze_pauli_twirling(
            results=reconstructed_results,
            qubits=self.qubits,
            gate_name=self.gate_name 
        )