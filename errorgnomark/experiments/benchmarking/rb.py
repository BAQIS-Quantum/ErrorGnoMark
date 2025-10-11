# File Path: errorgnomark/experiments/benchmarking/rb.py
# CORRECTED VERSION: Imports are fixed and EPG analysis is now centralized.

import numpy as np
from typing import List, Dict, Optional, Any
import matplotlib.pyplot as plt

# Framework imports (assuming these paths are correct based on your project structure)
from errorgnomark.engine import QuantumEngine
from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.experiments.base import BaseExperiment
# This assumes a CliffordGateSet class exists for generating random Cliffords.
# If the path is different, it should be adjusted.
from errorgnomark.circuits.gate_sets import CliffordGateSet

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# [[[ FIX: Corrected the import path to point to the actual analysis file ]]]
from errorgnomark.analysis.rb import fit_rb_data, analyze_epg, plot_rb_single, plot_rb_comparison
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv

class StandardRBExperiment(BaseExperiment):
    """
    Performs a standard Randomized Benchmarking (RB) experiment to find the Error Per Clifford (EPC).
    """
    def __init__(
        self,
        qubits: List[int],
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 30,
    ):
        super().__init__(qubits)
        self.circuits_per_depth = circuits_per_depth
        if depths is None:
            self.depths = [1, 10, 20, 40, 60, 80] if self.num_qubits == 1 else [1, 5, 10, 15, 20, 25]
        else:
            self.depths = depths
        self.gate_set = CliffordGateSet()
        self._circuits: List[QuantumCircuit] = []

    def generate_single_circuit(self, depth: int, seed: Optional[int] = None) -> QuantumCircuit:
        """Generates a single random Clifford sequence for a given depth."""
        rng = np.random.default_rng(seed)
        forward_gates, inverse_stack = [], []
        for _ in range(depth):
            layer_seed = rng.integers(2**32 - 1) if seed is not None else None
            fwd_layer, inv_layer = self.gate_set.get_random_clifford_and_inverse(self.qubits, seed=layer_seed)
            forward_gates.extend(fwd_layer)
            inverse_stack.append(inv_layer)
        inverse_gates = [gate for layer in reversed(inverse_stack) for gate in layer]
        circuit = QuantumCircuit(qubits=self.qubits, gates=forward_gates + inverse_gates)
        circuit.measure_all()
        return circuit

    def circuits(self) -> List[QuantumCircuit]:
        """Generates all circuits for the experiment."""
        if self._circuits:
            return self._circuits
        print(f"Generating {len(self.depths) * self.circuits_per_depth} circuits for Standard RB...")
        self._circuits = [self.generate_single_circuit(depth) for depth in self.depths for _ in range(self.circuits_per_depth)]
        return self._circuits

    def run(self, engine: QuantumEngine, shots: int = 4096, plot: bool = False, verbose: bool = True) -> Dict[str, Any]:
        """Executes the experiment, analyzes the data, and returns the results."""
        if verbose:
            print(f"--- Running Standard {self.num_qubits}-Qubit RB ---")
        
        raw_results = engine.execute(self.circuits(), shots=shots)
        
        survivals: Dict[int, List[float]] = {depth: [] for depth in self.depths}
        ground_state_str = '0' * self.num_qubits
        result_idx = 0
        for depth in self.depths:
            for _ in range(self.circuits_per_depth):
                _, noisy_counts = raw_results[result_idx]
                total_shots = sum(noisy_counts.values())
                prob = noisy_counts.get(ground_state_str, 0) / total_shots if total_shots > 0 else 0.0
                survivals[depth].append(prob)
                result_idx += 1
        
        if verbose: print("Fitting standard RB data...")
        fit_results = fit_rb_data(survivals, self.num_qubits)
        
        if verbose:
            if fit_results['fit_successful']:
                print(f"Fit successful. EPC = {fit_results['epc']:.3e}")
            else:
                print("Fit failed.")
        
        if plot:
            if verbose: print("Generating plot...")
            plot_rb_single(fit_results, self.num_qubits, title=f"Standard {self.num_qubits}-Qubit RB")
            
        return fit_results


class InterleavedRBExperiment(BaseExperiment):
    """
    Performs an Interleaved RB (IRB) experiment to find the error of a specific target gate.
    """
    def __init__(
        self,
        qubits: List[int],
        target_gate_name: str,
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 50,
    ):
        super().__init__(qubits)
        self.target_gate_name = target_gate_name.lower()
        self.target_gate = Gate(name=self.target_gate_name, qubits=tuple(qubits))
        self.circuits_per_depth = circuits_per_depth
        if len(self.target_gate.qubits) != self.num_qubits:
            raise ValueError(f"Target gate '{target_gate_name}' acts on {len(self.target_gate.qubits)} qubits, but experiment is for {self.num_qubits} qubits.")
        if depths is None:
            self.depths = [1, 10, 20, 30, 40, 50] if self.num_qubits == 1 else [1, 4, 8, 12, 16, 20]
        else:
            self.depths = depths
        self.gate_set = CliffordGateSet()
        self._circuits: List[QuantumCircuit] = []

    def generate_single_circuit(self, depth: int, seed: Optional[int] = None) -> QuantumCircuit:
        """Generates a single interleaved random Clifford sequence."""
        rng = np.random.default_rng(seed)
        forward_gates, inverse_stack = [], []
        interleaved_gate_inv = self.target_gate.inverse()
        
        for _ in range(depth):
            layer_seed = rng.integers(2**32 - 1) if seed is not None else None
            fwd_layer, inv_layer = self.gate_set.get_random_clifford_and_inverse(self.qubits, seed=layer_seed)
            
            forward_gates.extend(fwd_layer)
            forward_gates.append(self.target_gate) # Interleave the target gate
            
            inverse_stack.append([interleaved_gate_inv])
            inverse_stack.append(inv_layer)
            
        inverse_gates = [gate for layer in reversed(inverse_stack) for gate in layer]
        circuit = QuantumCircuit(qubits=self.qubits, gates=forward_gates + inverse_gates)
        circuit.measure_all()
        return circuit

    def circuits(self) -> List[QuantumCircuit]:
        """Generates all interleaved circuits for the experiment."""
        if self._circuits:
            return self._circuits
        print(f"Generating {len(self.depths) * self.circuits_per_depth} circuits for Interleaved RB...")
        self._circuits = [self.generate_single_circuit(depth) for depth in self.depths for _ in range(self.circuits_per_depth)]
        return self._circuits

    def run(self, engine: QuantumEngine, shots: int = 8096, plot: bool = False, verbose: bool = True) -> Dict[str, Any]:
        """Executes the full interleaved experiment, including the standard reference."""
        if verbose:
            print(f"\n--- Running Full Interleaved {self.num_qubits}-Qubit RB for gate '{self.target_gate_name}' ---")

        # Step 1: Run Standard RB experiment as a baseline
        if verbose: print("\n[Step 1/3] Running Standard RB reference experiment...")
        std_experiment = StandardRBExperiment(self.qubits, self.depths, self.circuits_per_depth)
        results_std = std_experiment.run(engine, shots=shots, plot=False, verbose=verbose)

        # Step 2: Run Interleaved RB experiment
        if verbose: print(f"\n[Step 2/3] Running Interleaved RB experiment with '{self.target_gate_name}'...")
        raw_results_int = engine.execute(self.circuits(), shots=shots)
        survivals_int: Dict[int, List[float]] = {depth: [] for depth in self.depths}
        ground_state_str = '0' * self.num_qubits
        result_idx = 0
        for depth in self.depths:
            for _ in range(self.circuits_per_depth):
                _, noisy_counts = raw_results_int[result_idx]
                total_shots = sum(noisy_counts.values())
                prob = noisy_counts.get(ground_state_str, 0) / total_shots if total_shots > 0 else 0.0
                survivals_int[depth].append(prob)
                result_idx += 1

        if verbose: print("Fitting interleaved RB data...")
        results_int = fit_rb_data(survivals_int, self.num_qubits)
        if verbose and results_int['fit_successful']:
            print(f"Fit successful. Interleaved EPC = {results_int['epc']:.3e}")

        # Step 3: Analyze results and calculate target gate error
        # REFACTORED: Use the centralized analysis function
        if verbose: print("\n[Step 3/3] Analyzing results and calculating EPG...")
        final_results = analyze_epg(results_std, results_int, self.num_qubits)
        gate_error = final_results['gate_error']

        if verbose:
            if not np.isnan(gate_error):
                print("\n--- Results ---")
                print(f"Calculated Error of gate '{self.target_gate_name}' (EPG) = {gate_error:.3e}")
            else:
                print("\nCould not calculate gate error because one or both fits failed.")

        if plot:
            if verbose: print("Generating comparison plot...")
            plot_rb_comparison(results_std, results_int, self.num_qubits, self.target_gate_name)

        return final_results