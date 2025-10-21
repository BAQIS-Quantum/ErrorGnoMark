# [CORRECTED VERSION v2.1 - Fixed TypeError on len(method) in refactored code]

import random
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import matplotlib.pyplot as plt

# --- Internal Framework Imports ---
try:
    from errorgnomark.engine import QuantumEngine
    from errorgnomark.circuits.circuit import Gate, QuantumCircuit
    from errorgnomark.circuits.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set
    from errorgnomark.analysis.xeb import analyze_xeb_and_spb_from_results, plot_xeb_decay
    from errorgnomark.analysis.spb import plot_spb_decay
except ImportError:
    # Fallback for standalone execution or testing
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    from errorgnomark.engine import QuantumEngine
    from errorgnomark.circuits.circuit import Gate, QuantumCircuit
    from errorgnomark.circuits.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set
    from errorgnomark.analysis.xeb import analyze_xeb_and_spb_from_results, plot_xeb_decay
    from errorgnomark.analysis.spb import plot_spb_decay

# A sentinel object to detect if an argument was provided or not.
_sentinel = object()

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

DEFAULT_NATIVE_GATES: List[str] = [
    'cz', 'sx', 'rz', 'h', 's' # Aligned with common superconducting bases
]

def _validate_list_of_integers(qubits: any, var_name: str):
    if not isinstance(qubits, list) or not all(isinstance(q, int) for q in qubits):
        raise TypeError(f"`{var_name}` must be a list of integers.")

class StandardXEBExperiment:
    """
    Generates and analyzes circuits for a standard Cross-Entropy Benchmarking (XEB) experiment.
    This class is aligned with the design patterns of StandardRBExperiment.
    """
    def __init__(self,
                 qubits: List[int],
                 depths: List[int] = [1, 5, 10, 15, 25, 40, 60],
                 circuits_per_depth: int = 30,
                 gate_set: Union[str, Dict, BaseGateSet] = "universal_xeb",
                 native_gates: Optional[List[str]] = DEFAULT_NATIVE_GATES,
                 seed: Optional[Union[int, float]] = None):
        _validate_list_of_integers(qubits, "qubits")
        self.qubits = qubits
        self.num_qubits = len(self.qubits)
        self.depths = depths
        self.circuits_per_depth = circuits_per_depth
        
        self.gate_set_spec = gate_set
        self.gate_set_obj = get_gate_set(self.gate_set_spec)
        
        self.topology = self._get_default_topology()
        self.native_gates = native_gates
        self.seed = seed
        self.results: Dict = {}
        self._circuits: Optional[List[QuantumCircuit]] = None

    def _get_default_topology(self) -> List[Tuple[int, int]]:
        """Generates a default linear topology for the qubits."""
        if len(self.qubits) < 2: return []
        return list(zip(self.qubits, self.qubits[1:]))

    def _generate_circuit(self, depth: int, seed: Optional[Union[int, float]], interleaved_gate: Optional[Gate] = None) -> QuantumCircuit:
        """
        Internal helper to generate one logical XEB circuit.
        This method is now agnostic to the specific gate set being used.
        """
        rng = random.Random(seed)
        circuit = QuantumCircuit(qubits=self.qubits)
        
        pattern_a = self.topology[0::2]
        pattern_b = self.topology[1::2]
        
        for d in range(depth):
            single_q_gates = self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random())
            circuit.add_gates(single_q_gates)

            if self.topology and isinstance(self.gate_set_obj, TwoQubitGateSet):
                pattern = pattern_a if d % 2 == 0 else pattern_b
                two_q_gates = self.gate_set_obj.get_random_2q_layer(pattern, seed=rng.random())
                circuit.add_gates(two_q_gates)
            
            if interleaved_gate:
                circuit.add_gate(interleaved_gate)

        final_single_q_gates = self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random())
        circuit.add_gates(final_single_q_gates)
        
        circuit.measure_all()
        
        circuit.metadata['depth'] = depth
        circuit.metadata['seed'] = seed
        if interleaved_gate:
            circuit.metadata['interleaved_gate_name'] = interleaved_gate.name
            
        return circuit

    def generate_single_circuit(self,
                                depth: int,
                                seed: Optional[Union[int, float]] = None,
                                interleaved_gate: Optional[Gate] = None) -> QuantumCircuit:
        """
        Generates a single XEB circuit for a given depth, decomposing it to native gates.
        This is a public-facing wrapper, mirroring the structure of StandardRBExperiment.
        """
        circuit = self._generate_circuit(depth, seed, interleaved_gate=interleaved_gate)
        
        if self.native_gates:
            circuit = circuit.decompose(basis_gates=self.native_gates)
            
        return circuit

    def circuits(self) -> List[QuantumCircuit]:
        """Generates all circuits for the full XEB experiment."""
        if self._circuits is None:
            all_circuits = []
            main_rng = random.Random(self.seed)
            
            for depth in self.depths:
                for _ in range(self.circuits_per_depth):
                    circuit_seed = main_rng.random()
                    circuit = self.generate_single_circuit(
                        depth=depth, 
                        seed=circuit_seed
                    )
                    all_circuits.append(circuit)
            self._circuits = all_circuits
        return self._circuits

    def run(self, engine: QuantumEngine, shots: int = 2048, plot: bool = True, axes: Optional[Tuple[plt.Axes, plt.Axes]] = None, **plot_kwargs) -> Dict[str, Any]:
        """Executes the full experiment and returns the analysis results."""
        xeb_type = "Interleaved" if isinstance(self, InterleavedXEBExperiment) else "Standard"
        logging.info(f"--- Running Dual Analysis {xeb_type} XEB on Qubits {self.qubits} ---")
        
        # ==============================================================================
        # === FIX: Added parentheses () to CALL the `circuits` method.               ===
        # === This ensures we get the list of circuits, not the method object itself. ===
        # ==============================================================================
        experiment_circuits = self.circuits()
        
        logging.info(f"Generated {len(experiment_circuits)} circuits. Executing on backend...")
        
        all_results_raw = engine.execute_with_ideal(experiment_circuits, shots)
        
        results_by_depth = defaultdict(list)
        for i, circuit in enumerate(experiment_circuits):
            depth = circuit.metadata.get('depth', self.depths[i // self.circuits_per_depth])
            results_by_depth[depth].append(all_results_raw[i])
            
        self.results = analyze_xeb_and_spb_from_results(results_by_depth, num_qubits=self.num_qubits)
        
        if plot:
            title = f"Dual Analysis on Qubits {self.qubits}"
            if xeb_type == "Interleaved":
                gate_name = getattr(self, 'interleaved_gate', Gate('?',(0,))).name
                title = f"Dual Interleaved Analysis for Gate '{gate_name}'"
            self._plot_results(axes, title=title, **plot_kwargs)
        return self.results

    def _plot_results(self, axes, title, **kwargs):
        """Helper method to plot both XEB and SPB decay curves."""
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
    Implements an Interleaved XEB experiment, inheriting the refactored logic.
    """
    def __init__(self,
                 qubits: List[int],
                 interleaved_gate: Gate,
                 depths: List[int] = [1, 5, 10, 15, 25, 40, 60],
                 circuits_per_depth: int = 30,
                 gate_set: Union[str, Dict, BaseGateSet] = "universal_xeb",
                 native_gates: Optional[List[str]] = DEFAULT_NATIVE_GATES,
                 seed: Optional[Union[int, float]] = None):
        super().__init__(qubits, depths, circuits_per_depth, gate_set, native_gates, seed)
        self.interleaved_gate = interleaved_gate

    def circuits(self) -> List[QuantumCircuit]:
        """Generates all circuits for the full Interleaved XEB experiment."""
        if self._circuits is None:
            all_circuits = []
            main_rng = random.Random(self.seed)
            
            for depth in self.depths:
                for _ in range(self.circuits_per_depth):
                    circuit_seed = main_rng.random()
                    circuit = self.generate_single_circuit(
                        depth=depth, 
                        seed=circuit_seed,
                        interleaved_gate=self.interleaved_gate
                    )
                    all_circuits.append(circuit)
            self._circuits = all_circuits
        return self._circuits

    def run(self, engine: QuantumEngine, shots: int = 2048, plot: bool = True, axes: Optional[Tuple[plt.Axes, plt.Axes]] = None) -> Dict[str, Any]:
        """Executes reference and interleaved experiments and calculates gate error."""
        logging.info(f"--- Running Full Dual Analysis Interleaved XEB for Gate '{self.interleaved_gate.name}' ---")
        
        logging.info("[Phase 1/2] Running Reference Experiment...")
        ref_experiment = StandardXEBExperiment(
            self.qubits, self.depths, self.circuits_per_depth, self.gate_set_spec, self.native_gates, self.seed
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
        """Plots a comparison of the reference and interleaved decay curves."""
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