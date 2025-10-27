# File Path: errorgnomark/experiments/characterization/tomography/state_tomography.py
# [CORRECTED VERSION - Fixes the engine call]

import itertools
from typing import List, Dict, Any, Optional
import numpy as np

from errorgnomark.engine import QuantumEngine
from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.experiments.base import BaseExperiment
from errorgnomark.analysis.tomography import StateTomographyAnalysis
from errorgnomark.analysis.result import ExperimentResult

class StateTomographyExperiment(BaseExperiment):
    """
    Performs state tomography on an N-qubit state prepared by a given circuit.
    This class is now optimized to use the engine's batch execution capabilities.
    """
    def __init__(self, qubits: List[int], state_prep_circuit: QuantumCircuit):
        super().__init__(qubits)
        if not isinstance(state_prep_circuit, QuantumCircuit):
            raise TypeError("state_prep_circuit must be a QuantumCircuit object.")
        
        self.state_prep_circuit = state_prep_circuit
        self.measurement_bases = ["".join(p) for p in itertools.product('XYZ', repeat=self.num_qubits)]
        self._circuits: List[QuantumCircuit] = []
        self.results: Dict[str, Any] = {}
        self.analysis_tool = StateTomographyAnalysis(self.qubits)

    def _create_measurement_circuit(self, basis: str) -> QuantumCircuit:
        tomo_circuit = self.state_prep_circuit.copy()
        tomo_circuit.metadata = {'basis': basis}
        for i, pauli_op in enumerate(basis):
            qubit = self.qubits[i]
            if pauli_op == 'X': tomo_circuit.add_gate(Gate('H', (qubit,)))
            elif pauli_op == 'Y':
                tomo_circuit.add_gate(Gate('SDG', (qubit,)))
                tomo_circuit.add_gate(Gate('H', (qubit,)))
        tomo_circuit.measure_all()
        return tomo_circuit

    @property
    def circuits(self) -> List[QuantumCircuit]:
        if not self._circuits:
            self._circuits = [self._create_measurement_circuit(basis) for basis in self.measurement_bases]
        return self._circuits

    def run(self, engine: QuantumEngine, shots: int, verbose: bool = False) -> Dict[str, Dict[str, int]]:
        if verbose: print(f"--- Running State Tomography Experiment ({self.num_qubits}-Qubit) ---")
        
        raw_counts_by_basis: Dict[str, Dict[str, int]] = {}
        exp_circuits = self.circuits
        
        # =========================================================================
        # [THE FIX IS HERE]
        # Changed engine.execute to engine.execute_with_ideal to match the
        # method name defined in the final version of engine.py.
        results_list = engine.execute_with_ideal(exp_circuits, shots)
        # =========================================================================
        
        for circuit, result_tuple in zip(exp_circuits, results_list):
            basis = circuit.metadata['basis']
            # The result_tuple is (ideal_probabilities, noisy_counts).
            # We correctly select the second element, which is the noisy counts.
            noisy_counts = result_tuple[1]
            raw_counts_by_basis[basis] = noisy_counts
        
        if verbose: print("\nRaw data collection complete.")
        self.results['raw_counts'] = raw_counts_by_basis
        self.results['shots'] = shots
        return raw_counts_by_basis

    def analyze(self, ideal_state: Optional[np.ndarray] = None, method: str = 'all') -> List[ExperimentResult]:
        if 'raw_counts' not in self.results:
            raise RuntimeError("Experiment has not been run yet. Call run() before analyze().")
            
        experiment_data_for_analysis = self._calculate_expectations()
        analysis_results = []
        
        ideal_rho = None
        if ideal_state is not None:
            ideal_rho = ideal_state if ideal_state.ndim == 2 else np.outer(ideal_state, ideal_state.conj())

        if method in ['linear', 'all']:
            res = self.analysis_tool.analyze_linear_inversion(experiment_data_for_analysis, ideal_rho=ideal_rho)
            analysis_results.append(res)
            
        if method in ['dfe', 'all'] and ideal_state is not None and ideal_state.ndim == 1:
            res = self.analysis_tool.analyze_dfe(experiment_data_for_analysis, ideal_statevector=ideal_state)
            analysis_results.append(res)
            
        if method in ['nesterov', 'all']:
            res = self.analysis_tool.analyze_with_nesterov(experiment_data_for_analysis, ideal_rho=ideal_rho)
            analysis_results.append(res)
            
        self.results['analysis_results'] = analysis_results
        return analysis_results

    def _calculate_expectations(self) -> Dict[str, Dict[str, Any]]:
        processed_data = {}
        raw_counts = self.results['raw_counts']
        
        for basis, counts in raw_counts.items():
            total_counts = sum(counts.values())
            probs = {outcome: count / total_counts for outcome, count in counts.items()} if total_counts > 0 else {}
            
            expectation = 0
            for outcome_str, prob in probs.items():
                parity = outcome_str.count('1')
                sign = (-1)**parity
                expectation += sign * prob
            
            processed_data[basis] = {'expectation': expectation, 'probabilities': probs}
        return processed_data