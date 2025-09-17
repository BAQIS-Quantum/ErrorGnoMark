# errorgnomark/experiments/benchmarking/mrb.py

import random
from typing import List, Tuple, Dict, Union, Callable

from ._base_benchmarking import _BaseBenchmarkingExperiment
from errorgnomark.circuits.circuit import QuantumCircuit, Gate # Import Gate
from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.analysis.benchmarking.mrb import fit_mrb_decay, plot_mrb_fit, plot_mrb_heatmap

class MirrorRBExperiment(_BaseBenchmarkingExperiment):
    """
    Implements Mirror Randomized Benchmarking (MRB).
    This class provides methods for both traditional decay-fitting analysis and
    a direct polarization computation with heatmap visualization.
    """
    def __init__(
        self,
        qubits: Union[List[int], List[Tuple[int, ...]]],
        depths: List[int],
        circuits_per_depth: int,
        gate_set: str = "clifford",
    ):
        super().__init__(qubits, depths, circuits_per_depth)
        
        from ..gate_sets import get_gate_set
        
        self.gate_set = get_gate_set(gate_set)

    def _calculate_survival_probability(self, counts: Dict[str, int], num_qubits: int) -> float:
        # This method is correct and unchanged
        total_shots = sum(counts.values())
        if total_shots == 0:
            return 0.0
        target_bitstring = '0' * num_qubits
        survival_counts = counts.get(target_bitstring, 0)
        return survival_counts / total_shots

    def _get_analysis_functions(self) -> Tuple[Callable, Callable]:
        # This method is correct and unchanged
        return fit_mrb_decay, plot_mrb_fit

    # ==============================================================================
    # --- [FIX] Added logic to handle N > 2 qubits without modifying gate_sets.py ---
    # ==============================================================================
    def _generate_single_circuit(self, group: Union[int, Tuple[int, ...]], depth: int) -> QuantumCircuit:
        """
        Generates a single mirrored circuit sequence. This now handles N > 2 qubits
        by manually constructing Clifford layers from primitive gates.
        """
        if isinstance(group, int):
            qubits = [group]
        else:
            qubits = list(group)
        
        num_qubits = len(qubits)
        random_sequence = []
        inverse_sequence = []

        for _ in range(depth):
            fwd_layer = []
            inv_layer = []

            if num_qubits <= 2:
                # Path for 1 and 2 qubits: Use the existing efficient method
                fwd_layer, inv_layer = self.gate_set.get_random_clifford_and_inverse(qubits)
            else:
                # Path for N > 2 qubits: Manually construct a Clifford layer and its inverse
                
                # 1. Forward Layer Construction
                # A "random" Clifford is a layer of 1Q Cliffords + an entangling layer
                fwd_1q_sublayer = self.gate_set.get_random_1q_layer(qubits)
                
                fwd_cnot_sublayer = []
                # Create a linear chain of CNOTs for entanglement
                for i in range(num_qubits - 1):
                    cnot_qubits = (qubits[i], qubits[i+1])
                    fwd_cnot_sublayer.append(Gate(self.gate_set.two_qubit_gate_name, cnot_qubits))
                
                fwd_layer = fwd_1q_sublayer + fwd_cnot_sublayer

                # 2. Inverse Layer Construction (in reverse order)
                # Inverse of CNOT layer (CNOT is self-inverse, just reverse gate order)
                inv_cnot_sublayer = list(reversed(fwd_cnot_sublayer))

                # Inverse of 1Q layer (get inverse gates and reverse order)
                inv_1q_sublayer = []
                for g in reversed(fwd_1q_sublayer):
                    # Access the inverse map from the gate set to find the inverse name
                    inv_name = self.gate_set._inverse_map.get(g.name)
                    if not inv_name:
                        raise KeyError(f"Cannot find inverse for gate '{g.name}'.")
                    inv_1q_sublayer.append(Gate(inv_name, g.qubits))
                
                inv_layer = inv_cnot_sublayer + inv_1q_sublayer

            # 3. Append the generated layers to the full sequences
            random_sequence.extend(fwd_layer)
            inverse_sequence = inv_layer + inverse_sequence

        all_gates = random_sequence + inverse_sequence
        circuit = QuantumCircuit(qubits=qubits, gates=all_gates)
        return circuit
    # --- [END FIX] ---

    @staticmethod
    def _compute_S(counts: Dict[str, int], num_qubits: int, target_bitstring: str) -> float:
        # This method is correct and unchanged
        if not target_bitstring:
            target_bitstring = '0' * num_qubits
        h_k = [0] * (num_qubits + 1)
        for bitstring, count in counts.items():
            if len(bitstring) != num_qubits: continue
            distance = sum(1 for a, b in zip(bitstring, target_bitstring) if a != b)
            if 0 <= distance <= num_qubits: h_k[distance] += count
        total_counts = sum(h_k)
        if total_counts == 0: return 0.0
        p_k = [hk / total_counts for hk in h_k]
        s_val = sum(((-1) ** k) * p_k[k] for k in range(num_qubits + 1))
        return max(0.0, min(s_val, 1.0))

    def run_and_compute_polarization(self, backend: BaseBackend, shots: int, verbose: bool = False) -> List[List[float]]:
        # This method is correct and unchanged
        all_polarizations = []
        for i, group in enumerate(self.qubits):
            num_qubits = len(group) if isinstance(group, tuple) else 1
            if verbose: print(f"\n--- Processing group: {group} ({i+1}/{len(self.qubits)}) ---")
            polarizations_per_depth = []
            for j, depth in enumerate(self.depths):
                if verbose: print(f"  Depth {depth} ({j+1}/{len(self.depths)}): [", end="", flush=True)
                sum_S = 0.0
                for k in range(self.circuits_per_depth):
                    circuit = self._generate_single_circuit(group, depth)
                    target_bitstring = '0' * num_qubits
                    _, noisy_counts = backend.run(circuit, shots=shots)
                    s_val = self._compute_S(noisy_counts, num_qubits, target_bitstring)
                    sum_S += s_val
                    if verbose: print(".", end="", flush=True)
                average_S = sum_S / self.circuits_per_depth
                polarizations_per_depth.append(average_S)
                if verbose: print(f"] Avg S = {average_S:.4f}")
            all_polarizations.append(polarizations_per_depth)
        return all_polarizations

    def run_direct_analysis(self, backend: BaseBackend, shots: int, verbose: bool = True, plot: bool = True, save_path: str = None) -> List[List[float]]:
        # This method is correct and unchanged
        print("=" * 60); print("    Running MRB Direct Polarization Analysis"); print("=" * 60)
        polarization_results = self.run_and_compute_polarization(backend, shots, verbose)
        print("\n\n" + "=" * 60); print("    Summary: Average Effective Polarization (S)"); print("=" * 60)
        header = "Qubit Group".ljust(15) + "\t" + "\t".join(map(str, self.depths))
        print(header); print("-" * len(header.expandtabs()))
        for i, group in enumerate(self.qubits):
            group_str = f"{str(group):<15}"
            results_str = "\t".join(f"{s:.4f}" for s in polarization_results[i])
            print(f"{group_str}\t{results_str}")
        if plot:
            print("\n[Plotting] Generating MRB performance heatmap...")
            plot_mrb_heatmap(polarization_results=polarization_results, qubit_groups=self.qubits, depths=self.depths, save_path=save_path)
        print("\nAnalysis complete.")
        return polarization_results