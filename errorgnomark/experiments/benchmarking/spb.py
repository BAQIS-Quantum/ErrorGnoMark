# File Path: errorgnomark/experiments/benchmarking/spb.py
#
# Implements Speckle Purity Benchmarking (SPB) within the errorgnomark framework,
# inheriting from BaseExperiment.

import numpy as np
from collections import defaultdict
from typing import List, Dict, Optional, Any

from errorgnomark.engine import QuantumEngine
from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.experiments.base import BaseExperiment
from errorgnomark.circuits.gate_sets import CliffordGateSet, get_gate_set
from errorgnomark.analysis.spb import (
    fit_spb_data,
    plot_spb_single,
    plot_spb_comparison,
    calculate_spb_gate_error
)

class SPBExperiment(BaseExperiment):
    """Performs a standard Speckle Purity Benchmarking (SPB) experiment."""
    def __init__(
        self,
        qubits: List[int],
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 30,
        gate_set: str = "clifford"
    ):
        super().__init__(qubits)
        self.depths = depths if depths is not None else list(range(10, 101, 10))
        self.circuits_per_depth = circuits_per_depth
        
        resolved_gate_set = get_gate_set(gate_set)
        if not isinstance(resolved_gate_set, CliffordGateSet):
            raise TypeError("SPB requires a 'CliffordGateSet'.")
        self.gate_set: CliffordGateSet = resolved_gate_set
        
        self._circuits: List[QuantumCircuit] = []
        self.results: Dict = {}

    def _generate_circuits(self):
        """Generates all random circuits for the SPB experiment."""
        self._circuits = []
        for depth in self.depths:
            for i in range(self.circuits_per_depth):
                circuit = QuantumCircuit(self.qubits)
                circuit.metadata = {'depth': depth, 'circuit_index': i}
                for _ in range(depth):
                    # For SPB, we only need the forward Clifford, not the inverse.
                    clifford_layer, _ = self.gate_set.get_random_clifford_and_inverse(self.qubits)
                    for gate in clifford_layer:
                        circuit.add_gate(gate)
                circuit.measure_all()
                self._circuits.append(circuit)

    @property
    def circuits(self) -> List[QuantumCircuit]:
        """Lazily generates and returns the list of circuits for the experiment."""
        if not self._circuits:
            self._generate_circuits()
        return self._circuits

    def _calculate_purity_from_counts(self, counts: Dict[str, int], shots: int) -> float:
        """Calculates purity using the standard UNBIASED ESTIMATOR for SPB."""
        if shots < 2: return np.nan
        n_i = np.array(list(counts.values()))
        N = shots
        # This is the defining formula for SPB purity.
        sum_p_sq_hat = np.sum(n_i * (n_i - 1)) / (N * (N - 1))
        return sum_p_sq_hat

    def run(self, engine: QuantumEngine, shots: int = 2000, verbose: bool = False, plot: bool = False) -> Dict:
        if verbose: print(f"--- Running Standard {self.num_qubits}-Qubit SPB ---")
        
        purities_by_depth = defaultdict(list)
        # Ensure circuits are generated before running
        exp_circuits = self.circuits
        
        for i, circuit in enumerate(exp_circuits):
            if verbose:
                print(f"\rRunning circuit {i+1}/{len(exp_circuits)} (Depth: {circuit.metadata['depth']})...", end='')
            
            _, counts = engine.run(circuit, shots)
            purity = self._calculate_purity_from_counts(counts, shots)
            if not np.isnan(purity):
                purities_by_depth[circuit.metadata['depth']].append(purity)
        
        if verbose: print("\nFitting SPB data...")
        self.results = fit_spb_data(purities_by_depth, self.num_qubits)
        
        if verbose:
            if self.results.get('fit_successful'):
                print(f"Fit successful. p_c = {self.results.get('p_c', 0):.5f}")
            else:
                print("Fit failed.")

        if plot:
            if verbose: print("Generating plot...")
            plot_spb_single(self.results, self.num_qubits)
            
        return self.results

class InterleavedSPBExperiment(SPBExperiment):
    """Performs an Interleaved SPB experiment to find the error of a specific target gate."""
    def __init__(
        self,
        qubits: List[int],
        target_gate_name: str,
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 30
    ):
        super().__init__(qubits, depths, circuits_per_depth)
        self.target_gate_name = target_gate_name.upper()
        self.target_gate = Gate(name=self.target_gate_name, qubits=tuple(self.qubits))

    def _generate_circuits(self):
        """Overrides parent method to generate interleaved circuits."""
        self._circuits = []
        for depth in self.depths:
            for i in range(self.circuits_per_depth):
                circuit = QuantumCircuit(self.qubits)
                circuit.metadata = {'depth': depth, 'circuit_index': i}
                for _ in range(depth):
                    clifford_layer, _ = self.gate_set.get_random_clifford_and_inverse(self.qubits)
                    for gate in clifford_layer:
                        circuit.add_gate(gate)
                    # The only difference: add the interleaved gate after each Clifford.
                    circuit.add_gate(self.target_gate)
                circuit.measure_all()
                self._circuits.append(circuit)

    def run(self, engine: QuantumEngine, shots: int = 2000, verbose: bool = False, plot: bool = False) -> Dict[str, Any]:
        if verbose: print(f"\n--- Running Interleaved {self.num_qubits}-Qubit SPB for gate '{self.target_gate_name}' ---")
        
        if verbose: print("[Phase 1/2] Running Standard SPB for baseline...")
        std_exp = SPBExperiment(self.qubits, self.depths, self.circuits_per_depth)
        results_std = std_exp.run(engine, shots, verbose, plot=False)
        
        if verbose: print(f"\n[Phase 2/2] Running Interleaved SPB with '{self.target_gate_name}'...")
        # This calls the run method from the parent (SPBExperiment), but because we have
        # overridden _generate_circuits, it will run with interleaved circuits.
        results_int = super().run(engine, shots, verbose, plot=False)

        if verbose: print("\nAnalyzing data...")
        gate_error_results = calculate_spb_gate_error(results_std, results_int, self.num_qubits)

        if verbose:
            if gate_error_results.get('calculation_successful'):
                print("\n--- Results ---")
                print(f"Standard p_c: {results_std.get('p_c'):.5f}, Interleaved p_c: {results_int.get('p_c'):.5f}")
                print(f"Gate Purity (p_G): {gate_error_results.get('p_G'):.5f}")
                print(f"Error of gate '{self.target_gate_name}' (r_G) = {gate_error_results.get('gate_error'):.3e}")
            else:
                print("\nCould not calculate gate error because one or both fits failed.")
        
        if plot:
            if verbose: print("Generating comparison plot...")
            plot_spb_comparison(results_std, results_int, self.num_qubits, self.target_gate_name)

        final_results = {**gate_error_results, 'standard_results': results_std, 'interleaved_results': results_int}
        return final_results