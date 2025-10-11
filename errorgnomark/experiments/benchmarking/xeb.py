# File Path: errorgnomark/experiments/benchmarking/xeb.py
# [FINAL LOGICALLY CORRECTED VERSION]

import itertools
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import matplotlib.pyplot as plt

from errorgnomark.engine import QuantumEngine
from errorgnomark.circuits.circuit import Gate, QuantumCircuit
from errorgnomark.experiments.base import BaseExperiment
from errorgnomark.circuits.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set
from errorgnomark.analysis.xeb import (
    analyze_xeb_fidelity,
    fit_xeb_fidelity_decay,
    calculate_interleaved_xeb_error,
    plot_xeb_decay
)

def _validate_list_of_integers(qubits: any, var_name: str):
    if not isinstance(qubits, list) or not all(isinstance(q, int) for q in qubits):
        raise TypeError(f"`{var_name}` must be a list of integers.")

class StandardXEBExperiment(BaseExperiment):
    def __init__(self,
                 qubits: List[int],
                 depths: List[int] = [1, 5, 10, 15, 25, 40, 60],
                 circuits_per_depth: int = 30,
                 gate_set: Union[str, Dict, BaseGateSet] = "clifford"):
        _validate_list_of_integers(qubits, "qubits")
        super().__init__(qubits)
        self.depths = depths
        self.circuits_per_depth = circuits_per_depth
        self.gate_set = get_gate_set(gate_set)
        self.topology = self._get_default_topology()
        self.results: Dict = {}

    @property
    def circuits(self) -> List[QuantumCircuit]:
        all_circuits = []
        for depth in self.depths:
            for i in range(self.circuits_per_depth):
                circuit_seed = abs(hash((depth, i, tuple(self.qubits)))) % (2**32)
                circuit = self._generate_circuit(depth, circuit_seed)
                all_circuits.append(circuit)
        return all_circuits

    def _get_default_topology(self) -> List[Tuple[int, int]]:
        if len(self.qubits) < 2: return []
        return list(itertools.combinations(self.qubits, 2))

    def _generate_circuit(self, depth: int, seed: Optional[int] = None) -> QuantumCircuit:
        master_rng = np.random.RandomState(seed)
        gates: List[Gate] = []
        for _ in range(depth):
            layer_seed_1q = master_rng.randint(2**32)
            gates.extend(self.gate_set.get_random_1q_layer(qubits=self.qubits, seed=layer_seed_1q))
            if self.topology and isinstance(self.gate_set, TwoQubitGateSet):
                layer_seed_2q = master_rng.randint(2**32)
                gates.extend(self.gate_set.get_random_2q_layer(topology=self.topology, seed=layer_seed_2q))
        return QuantumCircuit(qubits=self.qubits, gates=gates)

    def generate_single_circuit(self, depth: int, seed: Optional[int] = None) -> QuantumCircuit:
        return self._generate_circuit(depth, seed)

    def run_single_circuit(self, engine: QuantumEngine, shots: int, circuit: QuantumCircuit) -> float:
        ideal_probabilities, noisy_counts = engine.run(circuit, shots=shots)
        return analyze_xeb_fidelity(ideal_probabilities, noisy_counts)

    def run(self,
            engine: QuantumEngine,
            shots: int = 4096,
            plot: bool = True,
            verbose: bool = False) -> Dict:
        if verbose: print(f"--- Running Standard XEB on Qubits {self.qubits} ---")
        fidelities_by_depth = defaultdict(list)
        all_circuits = self.circuits
        if verbose:
            print(f"  Generated {len(all_circuits)} circuits across {len(self.depths)} depths.")
            print(f"  Running circuits with {shots} shots each...")
        for i, circuit in enumerate(all_circuits):
            depth = self.depths[i // self.circuits_per_depth]
            fidelity = self.run_single_circuit(engine, shots, circuit)
            fidelities_by_depth[depth].append(fidelity)
        if verbose: print("  Analysis: Fitting fidelity decay curve...")
        fit_results = fit_xeb_fidelity_decay(fidelities_by_depth)
        self.results = {
            'type': 'Standard XEB',
            'fit_results': fit_results,
            'raw_fidelities': dict(fidelities_by_depth)
        }
        if plot:
            fig, ax = plt.subplots(figsize=(10, 6))
            plot_xeb_decay(fidelities_by_depth, fit_results, ax=ax, label='Standard', color='blue')
            ax.set_title(f'Standard XEB Fidelity on Qubits {self.qubits}')
            ax.set_xlabel('Circuit Depth (Number of Cycles)')
            ax.set_ylabel('Linear XEB Fidelity')
            ax.set_ylim(-0.1, 1.1)
            ax.legend()
            ax.grid(True, linestyle=':')
            plt.tight_layout()
        return self.results

class InterleavedXEBExperiment(StandardXEBExperiment):
    def __init__(self,
                 qubits: List[int],
                 target_gate_name: str,
                 depths: List[int] = [1, 5, 10, 15, 25, 40, 60],
                 circuits_per_depth: int = 30,
                 gate_set: Union[str, Dict, BaseGateSet] = "clifford"):
        super().__init__(qubits, depths, circuits_per_depth, gate_set)
        self.target_gate_name = target_gate_name.lower()
        if len(self.qubits) != Gate(self.target_gate_name, self.qubits).arity:
            raise ValueError(f"Number of qubits provided ({len(self.qubits)}) does not match the arity of the target gate '{self.target_gate_name}'.")
        self.target_gate = Gate(self.target_gate_name, self.qubits)
        if self.target_gate.arity > 1 and not isinstance(self.gate_set, TwoQubitGateSet):
            raise TypeError(f"Cannot interleave a multi-qubit gate ('{self.target_gate_name}') with a gate set ('{gate_set}') that does not support two-qubit gates.")

    # [THE FINAL FIX] This method now correctly implements the "replace" logic.
    def _generate_circuit(self, depth: int, seed: Optional[int] = None) -> QuantumCircuit:
        # Step 1: Generate the standard, fully random circuit using the parent method.
        # This ensures the random part of the circuit is IDENTICAL to the baseline.
        standard_circuit = super()._generate_circuit(depth, seed)

        # Step 2: Identify the name of the random 2Q gate that needs to be replaced.
        # This requires the gate set to expose this information.
        try:
            # For CliffordGateSet, this attribute is 'two_qubit_gate_name'.
            gate_name_to_replace = self.gate_set.two_qubit_gate_name.lower()
        except AttributeError:
            raise AttributeError(
                f"The gate set '{self.gate_set.__class__.__name__}' used for interleaved XEB must have a "
                "'two_qubit_gate_name' attribute to identify which gates to replace."
            )

        # Step 3: Build the new list of gates, replacing the random 2Q gate with the target gate.
        interleaved_gates = []
        for gate in standard_circuit.gates:
            # Check if the current gate is the one we need to replace.
            if gate.arity == 2 and gate.name.lower() == gate_name_to_replace:
                # It's the random 2Q gate. Replace it with the target gate on the same qubits.
                # Note: This assumes the topology of the target gate matches the experiment's qubits.
                interleaved_gates.append(Gate(self.target_gate.name, gate.qubits))
            else:
                # It's a 1Q gate or a 2Q gate on a different pair, so we keep it.
                interleaved_gates.append(gate)
        
        return QuantumCircuit(qubits=self.qubits, gates=interleaved_gates)

    def run(self,
            engine: QuantumEngine,
            shots: int = 4096,
            plot: bool = True,
            verbose: bool = False) -> Dict:
        if verbose: print(f"--- Running Interleaved XEB for Gate '{self.target_gate_name.upper()}' on Qubits {self.qubits} ---")
        if verbose: print("\n[Phase 1/2] Running Standard XEB for baseline...")
        std_exp = StandardXEBExperiment(self.qubits, self.depths, self.circuits_per_depth, self.gate_set)
        std_results = std_exp.run(engine, shots, plot=False, verbose=verbose)
        if verbose: print(f"\n[Phase 2/2] Running Interleaved XEB with '{self.target_gate_name.upper()}'...")
        int_results = super().run(engine, shots, plot=False, verbose=verbose)
        if verbose: print("\nCalculating gate error from fit results...")
        
        # Check for valid fit results before calculation
        if 'p' not in std_results['fit_results'] or 'p' not in int_results['fit_results']:
             print("  > Warning: Could not calculate gate error due to failed fit in one of the experiments.")
             gate_error_results = {'error_per_gate': float('nan')}
        else:
            p_std = std_results['fit_results']['p']
            p_int = int_results['fit_results']['p']
            gate_error_results = calculate_interleaved_xeb_error(p_std, p_int, self.target_gate.arity)
        
        self.results = {
            'type': 'Interleaved XEB',
            'target_gate': self.target_gate_name,
            'gate_error_results': gate_error_results,
            'standard_results': std_results,
            'interleaved_results': int_results
        }
        if verbose:
            epg = gate_error_results.get('error_per_gate', float('nan'))
            print(f"  > Estimated Error per Gate ('{self.target_gate_name.upper()}'): {epg:.4f}")
        if plot:
            fig, ax = plt.subplots(figsize=(10, 7))
            plot_xeb_decay(std_results['raw_fidelities'], std_results['fit_results'], ax=ax, label='Standard', color='blue')
            plot_xeb_decay(int_results['raw_fidelities'], int_results['fit_results'], ax=ax, label='Interleaved', color='red')
            gate_error_val = gate_error_results.get('error_per_gate', float('nan'))
            title = (f"Interleaved XEB: '{self.target_gate_name.upper()}' on Qubits {self.qubits}\n"
                     f"Estimated Gate Error = {gate_error_val:.4f}")
            ax.set_title(title)
            ax.set_xlabel('Circuit Depth (Number of Cycles)')
            ax.set_ylabel('Linear XEB Fidelity')
            ax.set_ylim(-0.1, 1.1)
            ax.legend()
            ax.grid(True, linestyle=':')
            plt.tight_layout()
        return self.results