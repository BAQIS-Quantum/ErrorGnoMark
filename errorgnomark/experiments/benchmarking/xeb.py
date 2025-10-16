# File Path: errorgnomark/experiments/benchmarking/xeb.py
# [DEFINITIVE FINAL VERSION - Adapted to the RB-Optimized Engine]

import itertools
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import matplotlib.pyplot as plt

from errorgnomark.engine import QuantumEngine
from errorgnomark.circuits.circuit import Gate, QuantumCircuit
from errorgnomark.circuits.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set
from errorgnomark.analysis.xeb import (
    analyze_xeb_fidelity,
    fit_xeb_fidelity_decay,
    calculate_interleaved_xeb_error,
    plot_xeb_decay
)

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

DEFAULT_NATIVE_GATES: List[str] = [
    'cz', 'h', 's', 'sdg', 't', 'tdg', 'x', 'y', 'z', 'id',
    'rx', 'ry', 'rz'
]

def _validate_list_of_integers(qubits: any, var_name: str):
    if not isinstance(qubits, list) or not all(isinstance(q, int) for q in qubits):
        raise TypeError(f"`{var_name}` must be a list of integers.")

class StandardXEBExperiment:
    def __init__(self,
                 qubits: List[int],
                 depths: List[int] = [1, 5, 10, 15, 25, 40, 60],
                 circuits_per_depth: int = 30,
                 gate_set: Union[str, Dict, BaseGateSet] = "clifford",
                 native_gates: Optional[List[str]] = DEFAULT_NATIVE_GATES):
        _validate_list_of_integers(qubits, "qubits")
        self.qubits = qubits
        self.depths = depths
        self.circuits_per_depth = circuits_per_depth
        self.gate_set = get_gate_set(gate_set)
        self.topology = self._get_default_topology()
        self.native_gates = native_gates
        self.results: Dict = {}

        if self.native_gates is None:
            logging.info(f"XEB Experiment configured for LOGICAL view (`native_gates=None`). Decomposition is disabled.")
        else:
            logging.info(f"XEB Experiment configured for PHYSICAL view. Decomposing to native gates: {self.native_gates}")

    @property
    def circuits(self) -> List[QuantumCircuit]:
        all_circuits = []
        for depth in self.depths:
            for i in range(self.circuits_per_depth):
                circuit_seed = abs(hash((depth, i, tuple(self.qubits)))) % (2**32)
                circuit = self._generate_circuit(depth, circuit_seed)
                if self.native_gates:
                    circuit = circuit.decompose(basis_gates=self.native_gates)
                all_circuits.append(circuit)
        return all_circuits

    def _get_default_topology(self) -> List[Tuple[int, int]]:
        if len(self.qubits) < 2: return []
        return list(itertools.combinations(self.qubits, 2))

    def _generate_circuit(self, depth: int, seed: Optional[int] = None) -> QuantumCircuit:
        master_rng = np.random.default_rng(seed)
        gates: List[Gate] = []
        for _ in range(depth):
            seed_1q = master_rng.integers(2**32)
            gates.extend(self.gate_set.get_random_1q_layer(qubits=self.qubits, seed=seed_1q))
            if self.topology and isinstance(self.gate_set, TwoQubitGateSet):
                seed_2q = master_rng.integers(2**32)
                gates.extend(self.gate_set.get_random_2q_layer(topology=self.topology, seed=seed_2q))
        final_seed_1q = master_rng.integers(2**32)
        gates.extend(self.gate_set.get_random_1q_layer(qubits=self.qubits, seed=final_seed_1q))
        return QuantumCircuit(qubits=self.qubits, gates=gates)

    def generate_single_circuit(self, depth: int, seed: Optional[int] = None) -> QuantumCircuit:
        circuit = self._generate_circuit(depth, seed)
        if self.native_gates:
            circuit = circuit.decompose(basis_gates=self.native_gates)
        return circuit

    # <<< FIX: THIS METHOD IS NOW ADAPTED TO THE RB-OPTIMIZED ENGINE >>>
    def run_single_circuit(self, engine: QuantumEngine, shots: int, circuit: QuantumCircuit) -> float:
        """
        Calculates XEB fidelity for a single circuit using an engine that only provides counts.
        """
        # Step 1: Get the noisy measurement counts.
        # The engine's `run` or `execute` method provides this directly.
        # We need to call `backend.run` to get the counts, but the engine provides a wrapper.
        # To avoid batch overhead, we access the backend's primary run method.
        # Note: The chosen engine's `run` method returns only counts, which is not enough.
        # We must access the backend directly to get the full (ideal, noisy) tuple.
        ideal_probabilities, noisy_counts = engine.backend.run(circuit, shots=shots)

        # Step 2: Now that we have both pieces of data, call the analysis function.
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
        
        # We process circuits one by one because `run_single_circuit` now has special logic.
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
                 interleaved_gate: Gate,
                 depths: List[int] = [1, 5, 10, 15, 25, 40, 60],
                 circuits_per_depth: int = 30,
                 gate_set: Union[str, Dict, BaseGateSet] = "clifford",
                 native_gates: Optional[List[str]] = DEFAULT_NATIVE_GATES):
        super().__init__(qubits, depths, circuits_per_depth, gate_set, native_gates)
        self.interleaved_gate = interleaved_gate
        if self.interleaved_gate.arity > 1 and not isinstance(self.gate_set, TwoQubitGateSet):
            raise TypeError(
                f"Cannot interleave a multi-qubit gate ('{self.interleaved_gate.name}') "
                f"with a gate set ('{self.gate_set.__class__.__name__}') that does not support two-qubit gates."
            )

    def _generate_circuit(self, depth: int, seed: Optional[int] = None) -> QuantumCircuit:
        master_rng = np.random.default_rng(seed)
        gates: List[Gate] = []
        for i in range(depth):
            seed_1q = master_rng.integers(2**32)
            gates.extend(self.gate_set.get_random_1q_layer(qubits=self.qubits, seed=seed_1q))
            gates.append(self.interleaved_gate)
        final_seed_1q = master_rng.integers(2**32)
        gates.extend(self.gate_set.get_random_1q_layer(qubits=self.qubits, seed=final_seed_1q))
        return QuantumCircuit(qubits=self.qubits, gates=gates)

    def run(self,
            engine: QuantumEngine,
            shots: int = 4096,
            plot: bool = True,
            verbose: bool = False) -> Dict:
        gate_name = self.interleaved_gate.name.upper()
        if verbose: print(f"--- Running Interleaved XEB for Gate '{gate_name}' on Qubits {self.qubits} ---")
        if verbose: print("\n[Phase 1/2] Running Standard XEB for baseline...")
        std_exp = StandardXEBExperiment(self.qubits, self.depths, self.circuits_per_depth, self.gate_set, self.native_gates)
        std_results = std_exp.run(engine, shots, plot=False, verbose=verbose)
        if verbose: print(f"\n[Phase 2/2] Running Interleaved XEB with '{gate_name}'...")
        int_results = super().run(engine, shots, plot=False, verbose=verbose)
        if verbose: print("\nCalculating gate error from fit results...")
        if 'p' not in std_results['fit_results'] or 'p' not in int_results['fit_results']:
             print("  > Warning: Could not calculate gate error due to failed fit in one of the experiments.")
             gate_error_results = {'error_per_gate': float('nan')}
        else:
            p_std = std_results['fit_results']['p']
            p_int = int_results['fit_results']['p']
            gate_error_results = calculate_interleaved_xeb_error(p_std, p_int, self.interleaved_gate.arity)
        self.results = {
            'type': 'Interleaved XEB',
            'target_gate': self.interleaved_gate.name,
            'gate_error_results': gate_error_results,
            'standard_results': std_results,
            'interleaved_results': int_results
        }
        if verbose:
            epg = gate_error_results.get('error_per_gate', float('nan'))
            print(f"  > Estimated Error per Gate ('{gate_name}'): {epg:.4f}")
        if plot:
            fig, ax = plt.subplots(figsize=(10, 7))
            plot_xeb_decay(std_results['raw_fidelities'], std_results['fit_results'], ax=ax, label='Standard', color='blue')
            plot_xeb_decay(int_results['raw_fidelities'], int_results['fit_results'], ax=ax, label=f'Interleaved ({gate_name})', color='red')
            gate_error_val = gate_error_results.get('error_per_gate', float('nan'))
            title = (f"Interleaved XEB: '{gate_name}' on Qubits {self.qubits}\n"
                     f"Estimated Gate Error = {gate_error_val:.4f}")
            ax.set_title(title)
            ax.set_xlabel('Circuit Depth (Number of Cycles)')
            ax.set_ylabel('Linear XEB Fidelity')
            ax.set_ylim(-0.1, 1.1)
            ax.legend()
            ax.grid(True, linestyle=':')
            plt.tight_layout()
        return self.results