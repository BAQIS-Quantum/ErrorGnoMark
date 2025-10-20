# File Path: errorgnomark/experiments/benchmarking/xeb.py
# [DEFINITIVE FINAL VERSION - Targeted fix based on user-provided code]

import itertools
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import matplotlib.pyplot as plt

# --- Internal Framework Imports ---
try:
    from ..engine import QuantumEngine
    from ..circuits.circuit import Gate, QuantumCircuit
    from ..circuits.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set
    from ..analysis.xeb import analyze_xeb_and_spb_from_results, plot_xeb_decay
    from ..analysis.spb import plot_spb_decay
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from errorgnomark.engine import QuantumEngine
    from errorgnomark.circuits.circuit import Gate, QuantumCircuit
    from errorgnomark.circuits.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set
    from errorgnomark.analysis.xeb import analyze_xeb_and_spb_from_results, plot_xeb_decay
    from errorgnomark.analysis.spb import plot_spb_decay

# A sentinel object to detect if an argument was provided or not.
_sentinel = object()

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

DEFAULT_NATIVE_GATES: List[str] = [
    'cz', 'h', 's', 'sdg', 't', 'tdg', 'x', 'y', 'z', 'id',
    'rx', 'ry', 'rz'
]

def _validate_list_of_integers(qubits: any, var_name: str):
    if not isinstance(qubits, list) or not all(isinstance(q, int) for q in qubits):
        raise TypeError(f"`{var_name}` must be a list of integers.")

class StandardXEBExperiment:
    """
    Base class for XEB experiments, encapsulating circuit generation, execution, and analysis.
    """
    def __init__(self,
                 qubits: List[int],
                 depths: List[int] = [1, 5, 10, 15, 25, 40, 60],
                 circuits_per_depth: int = 30,
                 gate_set: Union[str, Dict, BaseGateSet] = "clifford",
                 native_gates: Optional[List[str]] = DEFAULT_NATIVE_GATES,
                 seed: Optional[int] = None):
        _validate_list_of_integers(qubits, "qubits")
        self.qubits = qubits
        self.num_qubits = len(self.qubits)
        self.depths = depths
        self.circuits_per_depth = circuits_per_depth
        
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        # [[[ FIX 1/2: Store the original gate_set input ]]]
        # We store the raw input 'gate_set' before it's processed. This allows us
        # to reliably check if the user requested "universal_xeb".
        self.gate_set_input = gate_set
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        self.gate_set_obj = get_gate_set(gate_set)
        
        self.topology = self._get_default_topology()
        self.native_gates = native_gates
        self.seed = seed
        self.results: Dict = {}
        self._circuits: Optional[List[QuantumCircuit]] = None

    def _get_default_topology(self) -> List[Tuple[int, int]]:
        if len(self.qubits) < 2: return []
        return list(zip(self.qubits, self.qubits[1:]))

    def _generate_circuit(self, depth: int, seed: Optional[int] = None, interleaved_gate: Optional[Gate] = None) -> QuantumCircuit:
        master_rng = np.random.default_rng(seed)
        gate_list: List[Gate] = []
        
        pattern_a = self.topology[0::2]
        pattern_b = self.topology[1::2]
        
        for d in range(depth):
            # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
            # [[[ FIX 2/2: Use the stored input for a reliable check ]]]
            # Instead of inspecting the gate_set_obj, we check the original input.
            # This guarantees that our special logic for "universal_xeb" is triggered.
            if self.gate_set_input == "universal_xeb":
                # If it is, we manually generate a layer of DECOMPOSABLE random gates (Rx, Rz)
                # instead of calling the method that produces the non-decomposable 'matrix_gate'.
                for q in self.qubits:
                    theta_rx = master_rng.uniform(0, 2 * np.pi)
                    theta_rz = master_rng.uniform(0, 2 * np.pi)
                    gate_list.append(Gate('rx', (q,), params=[theta_rx]))
                    gate_list.append(Gate('rz', (q,), params=[theta_rz]))
            else:
                # For all other gate sets (like "clifford"), we use the original, correct behavior.
                gate_list.extend(self.gate_set_obj.get_random_1q_layer(self.qubits, master_rng.integers(2**32)))
            # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

            if self.topology and isinstance(self.gate_set_obj, TwoQubitGateSet):
                pattern = pattern_a if d % 2 == 0 else pattern_b
                gate_list.extend(self.gate_set_obj.get_random_2q_layer(pattern, master_rng.integers(2**32)))
            if interleaved_gate:
                gate_list.append(interleaved_gate)

        # We apply the same logic for the final single-qubit layer
        if self.gate_set_input == "universal_xeb":
            for q in self.qubits:
                theta_rx = master_rng.uniform(0, 2 * np.pi)
                theta_rz = master_rng.uniform(0, 2 * np.pi)
                gate_list.append(Gate('rx', (q,), params=[theta_rx]))
                gate_list.append(Gate('rz', (q,), params=[theta_rz]))
        else:
            gate_list.extend(self.gate_set_obj.get_random_1q_layer(self.qubits, master_rng.integers(2**32)))
        
        circuit = QuantumCircuit(qubits=self.qubits, gates=gate_list)
        circuit.measure_all()
        
        circuit.metadata['logical_depth_m'] = depth
        circuit.metadata['seed'] = seed
        if interleaved_gate:
            circuit.metadata['interleaved'] = True
        return circuit

    def generate_single_circuit(self,
                                depth: int,
                                seed: Optional[int] = None,
                                native_gates: Optional[List[str]] = _sentinel,
                                interleaved_gate: Optional[Gate] = None) -> QuantumCircuit:
        circuit_seed = seed if seed is not None else np.random.default_rng().integers(2**32)
        circuit = self._generate_circuit(depth, circuit_seed, interleaved_gate=interleaved_gate)
        final_native_gates = self.native_gates if native_gates is _sentinel else native_gates
        if final_native_gates:
            return circuit.decompose(basis_gates=final_native_gates)
        return circuit

    @property
    def circuits(self) -> List[QuantumCircuit]:
        if self._circuits is None:
            all_circuits = []
            main_rng = np.random.default_rng(self.seed)
            for depth in self.depths:
                for _ in range(self.circuits_per_depth):
                    circuit_seed = main_rng.integers(2**32)
                    circuit = self.generate_single_circuit(depth, seed=circuit_seed)
                    all_circuits.append(circuit)
            self._circuits = all_circuits
        return self._circuits

    def run(self, engine: QuantumEngine, shots: int = 2048, plot: bool = True, axes: Optional[Tuple[plt.Axes, plt.Axes]] = None, **plot_kwargs) -> Dict[str, Any]:
        xeb_type = "Interleaved" if isinstance(self, InterleavedXEBExperiment) else "Standard"
        logging.info(f"--- Running Dual Analysis {xeb_type} XEB on Qubits {self.qubits} ---")
        
        experiment_circuits = self.circuits
        all_results_raw = engine.execute_with_ideal(experiment_circuits, shots)
        
        results_by_depth = defaultdict(list)
        for i, circuit in enumerate(experiment_circuits):
            depth = circuit.metadata.get('logical_depth_m', self.depths[i // self.circuits_per_depth])
            results_by_depth[depth].append(all_results_raw[i])
            
        self.results = analyze_xeb_and_spb_from_results(results_by_depth, num_qubits=self.num_qubits)
        
        if plot:
            title = f"Dual Analysis on Qubits {self.qubits}"
            if xeb_type == "Interleaved":
                title = f"Dual Interleaved Analysis for Gate '{self.interleaved_gate.name}'"
            self._plot_results(axes, title=title, **plot_kwargs)
        return self.results

    def _plot_results(self, axes, title, **kwargs):
        logging.info("Generating dual analysis plot...")
        show_plot_at_end = axes is None
        if axes is None:
            fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        ax1, ax2 = axes
        fig = ax1.get_figure()
        if show_plot_at_end: fig.suptitle(title, fontsize=16)
    
        plot_xeb_decay(self.results['xeb_analysis']['raw_data'], self.results['xeb_analysis']['fit_results'], ax=ax1, **kwargs)
        ax1.set_title("XEB Fidelity vs. Depth")
        ax1.legend()
        ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

        plot_spb_decay(self.results['spb_analysis']['raw_data'], self.results['spb_analysis']['fit_results'], ax=ax2, **kwargs)
        ax2.set_title("Speckle Purity vs. Depth")
        ax2.legend()
        ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

        if show_plot_at_end:
            fig.tight_layout(rect=[0, 0, 1, 0.96])
            plt.show()

class InterleavedXEBExperiment(StandardXEBExperiment):
    """
    Implements an Interleaved XEB experiment.
    """
    def __init__(self,
                 qubits: List[int],
                 interleaved_gate: Gate,
                 depths: List[int] = [1, 5, 10, 15, 25, 40, 60],
                 circuits_per_depth: int = 30,
                 gate_set: Union[str, Dict, BaseGateSet] = "clifford",
                 native_gates: Optional[List[str]] = DEFAULT_NATIVE_GATES,
                 seed: Optional[int] = None):
        super().__init__(qubits, depths, circuits_per_depth, gate_set, native_gates, seed)
        self.interleaved_gate = interleaved_gate

    def generate_single_circuit(self,
                                depth: int,
                                seed: Optional[int] = None,
                                native_gates: Optional[List[str]] = _sentinel) -> QuantumCircuit:
        return super().generate_single_circuit(
            depth=depth, seed=seed, native_gates=native_gates, interleaved_gate=self.interleaved_gate
        )

    def run(self, engine: QuantumEngine, shots: int = 2048, plot: bool = True, axes: Optional[Tuple[plt.Axes, plt.Axes]] = None) -> Dict[str, Any]:
        logging.info(f"--- Running Full Dual Analysis Interleaved XEB for Gate '{self.interleaved_gate.name}' ---")
        
        logging.info("[Phase 1/2] Running Reference Experiment...")
        ref_experiment = StandardXEBExperiment(
            self.qubits, self.depths, self.circuits_per_depth, self.gate_set_input, self.native_gates, self.seed
        )
        ref_analysis = ref_experiment.run(engine, shots=shots, plot=False)
        
        logging.info("[Phase 2/2] Running Interleaved Experiment...")
        int_analysis = super().run(engine, shots=shots, plot=False)

        p_ref = ref_analysis['xeb_analysis']['fit_results']['p']
        p_int = int_analysis['xeb_analysis']['fit_results']['p']
        
        num_interleaved_qubits = len(self.interleaved_gate.qubits)
        d = 2**num_interleaved_qubits
        gate_error = (d - 1) / d * (1 - p_int / p_ref) if p_ref > 0 else float('inf')
        
        self.results = {
            "reference": ref_analysis, "interleaved": int_analysis,
            "gate_error": gate_error, "gate_fidelity": 1 - gate_error,
        }
        
        if plot:
            self._plot_interleaved_results(axes)

        return self.results

    def _plot_interleaved_results(self, axes):
        logging.info("Generating dual analysis comparison plot...")
        show_plot_at_end = axes is None
        if axes is None:
            fig, axes = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
        
        ax1, ax2 = axes
        fig = ax1.get_figure()
        fig.suptitle(f"Dual Interleaved Analysis for Gate '{self.interleaved_gate.name}'", fontsize=16)
    
        ref_results = self.results['reference']
        plot_xeb_decay(ref_results['xeb_analysis']['raw_data'], ref_results['xeb_analysis']['fit_results'], ax=ax1, label='Reference', color='blue')
        plot_spb_decay(ref_results['spb_analysis']['raw_data'], ref_results['spb_analysis']['fit_results'], ax=ax2, label='Reference', color='blue')

        int_results = self.results['interleaved']
        plot_xeb_decay(int_results['xeb_analysis']['raw_data'], int_results['xeb_analysis']['fit_results'], ax=ax1, label='Interleaved', color='green')
        plot_spb_decay(int_results['spb_analysis']['raw_data'], int_results['spb_analysis']['fit_results'], ax=ax2, label='Interleaved', color='green')

        ax1.legend()
        ax2.legend()
        ax1.set_title("XEB Fidelity Comparison")
        ax2.set_title("Speckle Purity Comparison")
        ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

        if show_plot_at_end:
            fig.tight_layout(rect=[0, 0, 1, 0.96])
            plt.show()