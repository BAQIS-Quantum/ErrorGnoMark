# File Path: errorgnomark/experiments/benchmarking/rb.py
# [DEFINITIVE FINAL VERSION v3.7 - Patched for QuantumEngine v2 Interface]

import numpy as np
import random
import logging
from typing import List, Dict, Optional, Union

# --- Internal Framework Imports ---
try:
    import matplotlib.pyplot as plt
    from errorgnomark.circuits.circuit import QuantumCircuit, Gate
    from errorgnomark.engine import QuantumEngine
    from errorgnomark.analysis.rb import fit_rb_data, plot_rb_single, plot_rb_comparison, calculate_epg
    from errorgnomark.circuits.gate_sets import CliffordGateSet
except ImportError:
    # Fallback for standalone execution or testing
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    import matplotlib.pyplot as plt
    from errorgnomark.circuits.circuit import QuantumCircuit, Gate
    from errorgnomark.engine import QuantumEngine
    from errorgnomark.analysis.rb import fit_rb_data, plot_rb_single, plot_rb_comparison, calculate_epg
    from errorgnomark.circuits.gate_sets import CliffordGateSet

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Default values for experiment parameters ---
DEFAULT_RB_DEPTHS: List[int] = [1, 10, 20, 40, 60, 80, 100, 125] # Added more points for better fits
DEFAULT_CIRCUITS_PER_DEPTH: int = 25
EXAMPLE_NATIVE_GATES: List[str] = [
    'cz', 'sx', 'rz', 'h', 's'
]

class StandardRBExperiment:
    """
    Generates and analyzes circuits for a standard Randomized Benchmarking experiment.
    """
    def __init__(
        self,
        qubits: Union[int, List[int]],
        depths: List[int] = DEFAULT_RB_DEPTHS,
        circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
        native_gates: Optional[List[str]] = None,
        seed: Optional[Union[int, float]] = None
    ):
        self.qubits = [qubits] if isinstance(qubits, int) else qubits
        self.num_qubits = len(self.qubits)
        self.depths = depths
        self.circuits_per_depth = circuits_per_depth
        self.native_gates = native_gates
        self.seed = seed
        self.clifford_factory = CliffordGateSet()
        self.results: Dict = {}

        if self.native_gates:
            logging.info(f"RB Experiment configured for PHYSICAL view. Decomposing to: {self.native_gates}")
        else:
            logging.info(f"RB Experiment configured for LOGICAL view (`native_gates=None`).")

    def _generate_circuit(self, depth: int, seed: Optional[Union[int, float]], interleaved_gate: Optional[Gate] = None) -> QuantumCircuit:
        """
        Internal helper to generate one logical RB circuit. The protocol is correct.
        The recovery sequence ONLY inverts the random Cliffords.
        """
        rng = random.Random(seed)
        circuit = QuantumCircuit(qubits=self.qubits)
        
        all_clifford_inverses = []
        
        # Build the forward part of the circuit
        for _ in range(depth):
            fwd_gates, inv_gates = self.clifford_factory.get_random_clifford_and_inverse(
                self.qubits, seed=rng.random()
            )
            circuit.add_gates(fwd_gates)
            
            if interleaved_gate:
                circuit.add_gate(interleaved_gate)
                
            all_clifford_inverses.append(inv_gates)

        # Build the recovery part of the circuit by applying the inverses in reverse order.
        for clifford_inv_gates in reversed(all_clifford_inverses):
            circuit.add_gates(clifford_inv_gates)
        
        circuit.measure_all()
        # --- METADATA ---
        # This data is essential for the analysis and for the phenomenological backend.
        circuit.metadata['depth'] = depth
        circuit.metadata['seed'] = seed
        if interleaved_gate:
            circuit.metadata['interleaved_gate_name'] = interleaved_gate.name
            
        return circuit

    def generate_single_circuit(self, depth: int, seed: Optional[Union[int, float]] = None) -> QuantumCircuit:
        """
        Generates a single randomized benchmarking circuit for a given depth.
        This is a public-facing wrapper.
        """
        interleaved_gate = getattr(self, 'interleaved_gate', None)
        circuit = self._generate_circuit(depth, seed, interleaved_gate=interleaved_gate)
        
        if self.native_gates:
            circuit = circuit.decompose(basis_gates=self.native_gates)
            
        return circuit

    def circuits(self) -> List[QuantumCircuit]:
        """Generates all circuits for the full RB experiment."""
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
        return all_circuits

    def run(self, engine: QuantumEngine, shots: int, plot: bool = True, axes: Optional[plt.Axes] = None) -> Dict:
        """Executes the full experiment and returns the analysis results."""
        rb_type = "Interleaved" if isinstance(self, InterleavedRBExperiment) else "Standard"
        logging.info(f"--- Running {rb_type} {self.num_qubits}-Qubit RB ---")
        
        circs = self.circuits()
        logging.info(f"Generated {len(circs)} circuits. Executing on backend...")
        
        # ==============================================================================
        # ### FIX 1: Call the correct QuantumEngine method ###
        # The method `execute` was renamed to `execute_with_ideal` in the engine.
        # ==============================================================================
        results_list = engine.execute_with_ideal(circs, shots=shots)

        ground_state_str = '0' * self.num_qubits
        survivals = {d: [] for d in self.depths}
        
        for i, circuit in enumerate(circs):
            depth = circuit.metadata['depth']
            # ==============================================================================
            # ### FIX 2: Unpack the correct return tuple ###
            # `execute_with_ideal` returns a list of (ideal_probabilities, noisy_counts).
            # Your original code `_, noisy_counts` still works, but this is more explicit.
            # ==============================================================================
            _ideal_probs, noisy_counts = results_list[i]
            survival_prob = noisy_counts.get(ground_state_str, 0) / shots
            survivals[depth].append(survival_prob)
        
        logging.info(f"Fitting RB data...")
        fit_results = fit_rb_data(survivals=survivals, num_qubits=self.num_qubits)
        self.results = fit_results

        if fit_results["fit_successful"]:
            logging.info(f"Fit successful. EPC = {fit_results['epc']:.3e}")
        else:
            logging.warning("RB curve fitting failed.")

        if plot:
            show_plot_at_end = axes is None
            
            if fit_results["fit_successful"]:
                logging.info("Generating plot...")
                current_ax = axes if axes is not None else plt.subplots(figsize=(10, 6))[1]
                
                title = f"{rb_type} {self.num_qubits}Q RB Decay"
                plot_rb_single(fit_results, num_qubits=self.num_qubits, title=title, ax=current_ax)
                
                if show_plot_at_end:
                    plt.tight_layout()
                    plt.show()
            else:
                logging.warning("Skipping plot generation because fit failed.")
            
        return fit_results

class InterleavedRBExperiment(StandardRBExperiment):
    """Manages a full Interleaved Randomized Benchmarking (IRB) experiment."""
    def __init__(
        self,
        qubits: Union[int, List[int]],
        interleaved_gate: Gate,
        depths: List[int] = DEFAULT_RB_DEPTHS,
        circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
        native_gates: Optional[List[str]] = None,
        seed: Optional[Union[int, float]] = None
    ):
        super().__init__(
            qubits=qubits,
            depths=depths,
            circuits_per_depth=circuits_per_depth,
            native_gates=native_gates,
            seed=seed
        )
        self.interleaved_gate = interleaved_gate

    def run(self, engine: QuantumEngine, shots: int, plot: bool = True, axes: Optional[plt.Axes] = None) -> Optional[Dict]:
        """Executes reference and interleaved experiments to calculate EPG."""
        gate_name = self.interleaved_gate.name.upper()
        logging.info(f"\n--- Running Full Interleaved {self.num_qubits}-Qubit RB for gate '{gate_name}' ---")

        # --- Step 1: Run Standard RB Reference ---
        logging.info("[Step 1/3] Running Standard RB reference experiment...")
        std_rb_exp = StandardRBExperiment(
            qubits=self.qubits,
            depths=self.depths,
            circuits_per_depth=self.circuits_per_depth,
            native_gates=self.native_gates,
            seed=self.seed
        )
        # This call now correctly uses the patched StandardRBExperiment.run method
        results_std = std_rb_exp.run(engine, shots, plot=False)
        if not results_std.get("fit_successful"):
            logging.error("Standard RB reference experiment failed. Cannot proceed with Interleaved RB.")
            return None
        logging.info(f"Standard RB Reference Fit successful. EPC = {results_std['epc']:.3e}")

        # --- Step 2: Run Interleaved RB ---
        # The `super().run()` call will also use the patched run method from the base class.
        logging.info(f"\n[Step 2/3] Running Interleaved RB experiment with '{gate_name}'...")
        results_interleaved = super().run(engine, shots=shots, plot=False)
        if not results_interleaved.get("fit_successful"):
            logging.error("Interleaved RB fitting failed.")
            return None
        
        # --- Step 3: Analyze and Plot ---
        logging.info("\n[Step 3/3] Analyzing results and calculating EPG...")
        epg = calculate_epg(results_std['p'], results_interleaved['p'], self.num_qubits)
        
        logging.info("\n--- IRB Results ---")
        logging.info(f"Reference EPC (Error per Clifford) = {results_std['epc']:.3e}")
        logging.info(f"Interleaved EPC (Error per Clifford+Gate) = {results_interleaved['epc']:.3e}")
        logging.info(f"==> Calculated Error of gate '{gate_name}' (EPG) = {epg:.3e} <==")

        if plot:
            logging.info("Generating comparison plot...")
            show_plot_at_end = axes is None
            current_ax = axes if axes is not None else plt.subplots(figsize=(10, 6))[1]

            plot_rb_comparison(
                results_std, results_interleaved,
                num_qubits=self.num_qubits, target_gate_name=gate_name, ax=current_ax
            )
            
            if show_plot_at_end:
                plt.tight_layout()
                plt.show()
        
        self.results = {
            "epg": epg, 
            "standard_results": results_std, 
            "interleaved_results": results_interleaved
        }
        return self.results