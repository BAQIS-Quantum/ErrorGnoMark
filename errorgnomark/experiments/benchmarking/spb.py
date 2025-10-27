# File Path: errorgnomark/experiments/benchmarking/spb.py
#
# [COMPATIBILITY UPDATE v3.0 - Aligned with XEBExperiment interface]

import numpy as np
from collections import defaultdict
from typing import List, Dict, Optional, Any

from errorgnomark.engine import QuantumEngine
from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.experiments.base import BaseExperiment
from errorgnomark.circuits.gate_sets import CliffordGateSet, get_gate_set
# Imports are now correct and fully compatible
from errorgnomark.analysis.spb import (
    _calculate_purity_from_counts,
    fit_spb_data,
    plot_spb_decay,
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
        if depths is None:
            self.depths = list(range(5, 101, 10)) if self.num_qubits == 1 else list(range(4, 41, 4))
        else:
            self.depths = depths
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
                circuit.metadata = {'depth': depth, 'circuit_index': i, 'type': 'standard'}
                for _ in range(depth):
                    clifford_layer, _ = self.gate_set.get_random_clifford_and_inverse(self.qubits)
                    circuit.add_gates(clifford_layer)
                circuit.measure_all()
                self._circuits.append(circuit)

    @property
    def circuits(self) -> List[QuantumCircuit]:
        if not self._circuits:
            self._generate_circuits()
        return self._circuits

    def run(self, engine: QuantumEngine, shots: int = 2000, verbose: bool = False, plot: bool = False) -> Dict:
        if verbose: print(f"--- Running Standard {self.num_qubits}-Qubit SPB ---")
        
        purities_by_depth = defaultdict(list)
        for i, circuit in enumerate(self.circuits):
            if verbose: print(f"\rRunning circuit {i+1}/{len(self.circuits)}...", end='')
            _, counts = engine.run(circuit, shots)
            purity = _calculate_purity_from_counts(counts, shots)
            if not np.isnan(purity):
                purities_by_depth[circuit.metadata['depth']].append(purity)
        
        if verbose: print("\nFitting SPB data...")
        self.results = fit_spb_data(purities_by_depth, self.num_qubits)
        
        if verbose and self.results.get('fit_successful'):
            p_c = self.results.get('fit_results', {}).get('p_c', 0)
            print(f"Fit successful. p_c = {p_c:.5f}")
        elif verbose:
            print("Fit failed.")

        if plot and self.results.get('fit_successful'):
            # [COMPATIBILITY UPDATE] Call plot_spb_decay with the correct signature
            plot_spb_decay(
                raw_data=self.results['raw_data'],
                fit_results=self.results['fit_results'],
                title=f"{self.num_qubits}-Qubit Standard SPB"
            )
            
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
        self.target_gate = Gate(name=self.target_gate_name, qubits=self.qubits)

    def _generate_circuits(self):
        """Overrides parent method to generate interleaved circuits."""
        self._circuits = []
        for depth in self.depths:
            for i in range(self.circuits_per_depth):
                circuit = QuantumCircuit(self.qubits)
                circuit.metadata = {'depth': depth, 'circuit_index': i, 'type': 'interleaved'}
                for _ in range(depth):
                    clifford_layer, _ = self.gate_set.get_random_clifford_and_inverse(self.qubits)
                    circuit.add_gates(clifford_layer)
                    circuit.add_gate(self.target_gate)
                circuit.measure_all()
                self._circuits.append(circuit)

    def run(
        self,
        engine: QuantumEngine,
        shots: int = 2000,
        standard_results: Optional[Dict] = None,
        verbose: bool = False,
        plot: bool = False
    ) -> Dict[str, Any]:
        if standard_results is None:
            if verbose: print("[Phase 1/2] Running Standard SPB for baseline...")
            std_exp = SPBExperiment(self.qubits, self.depths, self.circuits_per_depth)
            results_std = std_exp.run(engine, shots, verbose=verbose, plot=False)
        else:
            if verbose: print("[Phase 1/2] Using provided Standard SPB results for baseline.")
            results_std = standard_results
        
        if verbose: print(f"\n[Phase 2/2] Running Interleaved SPB with '{self.target_gate_name}'...")
        results_int = super().run(engine, shots, verbose=verbose, plot=False)

        if verbose: print("\nAnalyzing data...")
        gate_error_results = calculate_spb_gate_error(results_std, results_int, self.num_qubits)

        if verbose and gate_error_results.get('calculation_successful'):
            p_c_std = results_std.get('fit_results', {}).get('p_c')
            p_c_int = results_int.get('fit_results', {}).get('p_c')
            print("\n--- Results ---")
            print(f"Standard p_c: {p_c_std:.5f}, Interleaved p_c: {p_c_int:.5f}")
            print(f"Gate Purity (p_G): {gate_error_results.get('p_G'):.5f}")
            print(f"Error of gate '{self.target_gate_name}' (r_G) = {gate_error_results.get('gate_error'):.3e}")
        elif verbose:
            print("\nCould not calculate gate error: " + gate_error_results.get('reason', 'Unknown reason.'))
        
        if plot:
            if verbose: print("Generating comparison plot...")
            # [COMPATIBILITY UPDATE] Call plot_spb_comparison with the correct signature
            plot_spb_comparison(results_std, results_int, self.num_qubits, self.target_gate_name)

        final_results = {**gate_error_results, 'standard_results': results_std, 'interleaved_results': results_int}
        return final_results