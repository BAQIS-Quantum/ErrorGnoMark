# File Path: errorgnomark/experiments/benchmarking/prb.py
# [FINAL VERSION - Aligned with robust analysis and framework structure]

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np

from errorgnomark.engine import QuantumEngine
from errorgnomark.circuits.circuit import Gate, QuantumCircuit
from errorgnomark.experiments.base import BaseExperiment
from errorgnomark.circuits.gate_sets import CliffordGateSet, get_gate_set
from errorgnomark.analysis.prb import (
    fit_prb_data,
    plot_prb_single,
    plot_prb_comparison,
    calculate_prb_gate_error
)

class StandardPRBExperiment(BaseExperiment):
    def __init__(
        self,
        qubits: List[int],
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 30,
        gate_set: str = "clifford",
    ):
        super().__init__(qubits)
        self.circuits_per_depth = circuits_per_depth
        
        if depths is None:
            self.depths = [1, 10, 20, 40, 60, 80] if self.num_qubits == 1 else [1, 5, 10, 15, 20, 25]
        else:
            self.depths = depths
        
        resolved_gate_set = get_gate_set(gate_set)
        if not isinstance(resolved_gate_set, CliffordGateSet):
            raise TypeError("Purity RB requires a 'CliffordGateSet'.")
        self.gate_set: CliffordGateSet = resolved_gate_set
        
        self.results: Dict = {}

    @property
    def circuits(self) -> List[QuantumCircuit]:
        raise NotImplementedError("Purity RB generates circuit pairs dynamically.")

    def _generate_circuit_pair(self, depth: int, seed: Optional[int] = None) -> Tuple[QuantumCircuit, QuantumCircuit]:
        master_rng = np.random.RandomState(seed)
        forward_gates: List[Gate] = []
        
        for _ in range(depth):
            layer_seed = master_rng.randint(2**32)
            fwd_layer, _ = self.gate_set.get_random_clifford_and_inverse(self.qubits, seed=layer_seed)
            forward_gates.extend(fwd_layer)

        inverse_gates = [gate.inverse() for gate in reversed(forward_gates)]
        twirl_seed = master_rng.randint(2**32)
        twirling_gates = self.gate_set.get_random_pauli_layer(self.qubits, seed=twirl_seed)
        
        circuit_a = QuantumCircuit(qubits=self.qubits, gates=forward_gates + inverse_gates + twirling_gates)
        circuit_a.measure_all()
        
        circuit_b = QuantumCircuit(qubits=self.qubits, gates=forward_gates + inverse_gates)
        circuit_b.measure_all()
        
        return circuit_a, circuit_b

    def run(self, engine: QuantumEngine, shots: int = 4096, verbose: bool = False, plot: bool = False) -> Dict:
        if verbose:
            print(f"--- Running Standard {self.num_qubits}-Qubit Purity RB ---")
        
        purities_by_depth = defaultdict(list)
        total_pairs = len(self.depths) * self.circuits_per_depth
        
        count = 0
        for depth in self.depths:
            for i in range(self.circuits_per_depth):
                count += 1
                if verbose:
                    print(f"Running circuit pair {count}/{total_pairs} (Depth: {depth})...", end='\r')
                
                pair_seed = abs(hash((depth, i, tuple(self.qubits)))) % (2**32)
                circuit_a, circuit_b = self._generate_circuit_pair(depth, seed=pair_seed)
                
                _, noisy_counts_a = engine.run(circuit_a, shots)
                _, noisy_counts_b = engine.run(circuit_b, shots)

                total_shots_a = sum(noisy_counts_a.values())
                total_shots_b = sum(noisy_counts_b.values())
                
                purity = float('nan')
                if total_shots_a > 0 and total_shots_b > 0:
                    prob_a = noisy_counts_a.get('0' * self.num_qubits, 0) / total_shots_a
                    prob_b = noisy_counts_b.get('0' * self.num_qubits, 0) / total_shots_b
                    purity = 2 * prob_a - prob_b
                
                if not np.isnan(purity):
                    purities_by_depth[depth].append(purity)
        
        if verbose: print("\nFitting standard Purity RB data...")
        fit_results = fit_prb_data(purities_by_depth, self.num_qubits)
        
        if verbose:
            if fit_results.get('fit_successful'):
                print(f"Fit successful. Purity Alpha = {fit_results['alpha']:.3e}")
            else:
                print("Fit failed.")
        
        self.results = fit_results
        
        if plot:
            if verbose: print("Generating plot...")
            plot_prb_single(self.results, self.num_qubits)
            
        return self.results

class InterleavedPRBExperiment(StandardPRBExperiment):
    def __init__(
        self,
        qubits: List[int],
        target_gate_name: str,
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 30,
    ):
        super().__init__(qubits, depths, circuits_per_depth)
        self.target_gate_name = target_gate_name.upper() # Use uppercase for consistency
        self.target_gate = Gate(name=self.target_gate_name, qubits=tuple(self.qubits))

        if len(self.target_gate.qubits) != self.num_qubits:
            raise ValueError(f"Target gate acts on {len(self.target_gate.qubits)} qubits, but experiment is for {self.num_qubits}.")
        
        if depths is None:
            self.depths = [1, 10, 20, 30, 40, 50] if self.num_qubits == 1 else [1, 4, 8, 12, 16, 20]

    def _generate_circuit_pair(self, depth: int, seed: Optional[int] = None) -> Tuple[QuantumCircuit, QuantumCircuit]:
        master_rng = np.random.RandomState(seed)
        forward_gates: List[Gate] = []
        
        for _ in range(depth):
            layer_seed = master_rng.randint(2**32)
            fwd_layer, _ = self.gate_set.get_random_clifford_and_inverse(self.qubits, seed=layer_seed)
            forward_gates.extend(fwd_layer)
            forward_gates.append(self.target_gate)

        inverse_gates = [gate.inverse() for gate in reversed(forward_gates)]
        twirl_seed = master_rng.randint(2**32)
        twirling_gates = self.gate_set.get_random_pauli_layer(self.qubits, seed=twirl_seed)
        
        circuit_a = QuantumCircuit(qubits=self.qubits, gates=forward_gates + inverse_gates + twirling_gates)
        circuit_a.measure_all()
        
        circuit_b = QuantumCircuit(qubits=self.qubits, gates=forward_gates + inverse_gates)
        circuit_b.measure_all()
        
        return circuit_a, circuit_b

    def run(self, engine: QuantumEngine, shots: int = 4096, verbose: bool = False, plot: bool = False) -> Dict:
        if verbose:
            print(f"\n--- Running Interleaved {self.num_qubits}-Qubit Purity RB for gate '{self.target_gate_name}' ---")

        if verbose: print("\n[Phase 1/2] Running Standard Purity RB for baseline...")
        std_exp = StandardPRBExperiment(self.qubits, self.depths, self.circuits_per_depth)
        results_std = std_exp.run(engine, shots, verbose, plot=False)

        if verbose: print(f"\n[Phase 2/2] Running Interleaved Purity RB with '{self.target_gate_name}'...")
        # This calls the overridden _generate_circuit_pair method correctly
        results_int = super().run(engine, shots, verbose, plot=False) 

        if verbose: print("\nCalculating gate error from fit results...")
        gate_error_results = calculate_prb_gate_error(results_std, results_int)
        
        if verbose:
            if gate_error_results.get('calculation_successful'):
                print(f"  > Estimated Error per Gate ('{self.target_gate_name}'): {gate_error_results['gate_error']:.3e}")
            else:
                print("  > Gate error calculation failed.")

        if plot:
            if verbose: print("Generating comparison plot...")
            plot_prb_comparison(results_std, results_int, self.num_qubits, self.target_gate_name)

        final_results = {**gate_error_results, 'standard_results': results_std, 'interleaved_results': results_int}
        return final_results