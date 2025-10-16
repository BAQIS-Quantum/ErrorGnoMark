# File Path: errorgnomark/experiments/benchmarking/rb.py
# [DEFINITIVE FINAL VERSION v10 - Implemented Default Native Gates]

import numpy as np
import random
from typing import List, Dict, Optional, Union
import logging
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# <<< CHANGE 1: DEFINING THE DEFAULT NATIVE GATE SET >>>
# This list represents a common gate set for CZ-based superconducting platforms.
# CNOT is NOT in this list, so it will be decomposed by default.
DEFAULT_NATIVE_GATES: List[str] = [
    'cz', 'h', 's', 'sdg', 't', 'tdg', 'x', 'y', 'z', 'id',
    'rx', 'ry', 'rz' # Using generic rotations is often more practical
]

try:
    from errorgnomark.circuits.circuit import QuantumCircuit, Gate
    from errorgnomark.engine import QuantumEngine
    from errorgnomark.analysis.rb import fit_rb_data, analyze_epg, plot_rb_single, plot_rb_comparison, calculate_epg
    from errorgnomark.circuits.gate_sets import CliffordGateSet
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    from errorgnomark.circuits.circuit import QuantumCircuit, Gate
    from errorgnomark.engine import QuantumEngine
    from errorgnomark.analysis.rb import fit_rb_data, analyze_epg, plot_rb_single, plot_rb_comparison, calculate_epg
    from errorgnomark.circuits.gate_sets import CliffordGateSet


class StandardRBExperiment:
    """
    Generates and analyzes circuits for a standard Randomized Benchmarking experiment.
    By default, decomposes circuits to a CZ-based gate set.
    To get a logical view, explicitly pass `native_gates=None`.
    """
    def __init__(
        self,
        qubits: Union[int, List[int]],
        depths: List[int],
        num_sequences: int = 30,
        # <<< CHANGE 2: UPDATING THE DEFAULT VALUE FOR NATIVE_GATES >>>
        native_gates: Optional[List[str]] = DEFAULT_NATIVE_GATES,
        interleaved_gate: Optional[Gate] = None
    ):
        self.qubits = [qubits] if isinstance(qubits, int) else qubits
        self.num_qubits = len(self.qubits)
        self.depths = depths
        self.num_sequences_per_depth = num_sequences
        self.native_gates = native_gates
        self.interleaved_gate = interleaved_gate
        self.clifford_factory = CliffordGateSet()

        # <<< CHANGE 3: UPDATING THE LOGIC FOR LOGGING MESSAGES >>>
        if self.native_gates is None:
            # This now only happens when the user explicitly passes native_gates=None
            logging.info(f"Experiment configured for LOGICAL view (`native_gates=None`). Decomposition is disabled.")
        else:
            # This is now the default behavior
            logging.info(f"Experiment configured for PHYSICAL view. Decomposing to native gates: {self.native_gates}")

    def circuits(self) -> List[QuantumCircuit]:
        """Generates all RB circuits for the experiment."""
        all_circuits = []
        for depth in self.depths:
            for i in range(self.num_sequences_per_depth):
                seed = hash((depth, i, tuple(self.qubits), self.interleaved_gate.name if self.interleaved_gate else ''))
                rng = random.Random(seed)
                circuit = QuantumCircuit(qubits=self.qubits)
                all_inverse_gate_lists = []
                
                for _ in range(depth):
                    try:
                        fwd_gates, inv_gates = self.clifford_factory.get_random_clifford_and_inverse(
                            self.qubits, seed=rng.random()
                        )
                    except ValueError as e:
                        raise NotImplementedError(f"RB is not supported for {self.num_qubits} qubits. Original error: {e}") from e

                    for gate in fwd_gates:
                        circuit.add_gate(gate)
                    if self.interleaved_gate:
                        circuit.add_gate(self.interleaved_gate)
                    all_inverse_gate_lists.append(inv_gates)

                interleaved_gate_inv = self.interleaved_gate.inverse() if self.interleaved_gate else None
                for inv_gate_list in reversed(all_inverse_gate_lists):
                    if self.interleaved_gate:
                        circuit.add_gate(interleaved_gate_inv)
                    for gate in inv_gate_list:
                        circuit.add_gate(gate)
                
                circuit.measure_all()
                if self.native_gates:
                    circuit = circuit.decompose(basis_gates=self.native_gates)
                all_circuits.append(circuit)
        return all_circuits

    def run(self, engine: QuantumEngine, shots: int = 1024, plot: bool = False, verbose: bool = True) -> Dict:
        """Executes the RB experiment, preprocesses data, and returns analysis results."""
        rb_type = "Interleaved" if self.interleaved_gate else "Standard"
        if verbose:
            print(f"--- Running {rb_type} {self.num_qubits}-Qubit RB ---")
        
        circs = self.circuits()
        if verbose:
            print(f"Generating {len(circs)} circuits for {rb_type} RB...")
        
        raw_results = engine.execute(circs, shots=shots)
        
        ground_state_str = '0' * self.num_qubits
        survivals = {d: [] for d in self.depths}
        result_index = 0
        for depth in self.depths:
            for _ in range(self.num_sequences_per_depth):
                counts = raw_results[result_index]
                survival_prob = counts.get(ground_state_str, 0) / shots
                survivals[depth].append(survival_prob)
                result_index += 1
        
        if verbose:
            print(f"Fitting {rb_type.lower()} RB data...")
        
        fit_results = fit_rb_data(
            survivals=survivals,
            num_qubits=self.num_qubits
        )

        if fit_results["fit_successful"]:
            logging.info(f"Fit successful. EPC = {fit_results['epc']:.3e}")
        else:
            logging.warning("RB curve fitting failed.")

        if plot and fit_results["fit_successful"]:
            if verbose:
                print("Generating plot...")
            title = f"{rb_type} {self.num_qubits}Q RB Decay"
            fig = plot_rb_single(fit_results, num_qubits=self.num_qubits, title=title)
            fig.show()
            
        return fit_results


class InterleavedRBExperiment:
    """Manages a full Interleaved Randomized Benchmarking (IRB) experiment."""
    def __init__(
        self,
        qubits: Union[int, List[int]],
        interleaved_gate: Gate,
        depths: List[int],
        num_sequences: int = 30,
        native_gates: Optional[List[str]] = DEFAULT_NATIVE_GATES
    ):
        self.qubits = [qubits] if isinstance(qubits, int) else qubits
        self.num_qubits = len(self.qubits)
        self.interleaved_gate = interleaved_gate
        self.depths = depths
        self.num_sequences = num_sequences
        self.native_gates = native_gates

        if self.native_gates is None:
            logging.info(f"IRB Experiment configured for LOGICAL view (`native_gates=None`). Decomposition is disabled.")
        else:
            logging.info(f"IRB Experiment configured for PHYSICAL view. Decomposing to native gates: {self.native_gates}")

    def run(self, engine: QuantumEngine, shots: int = 1024, plot: bool = False, verbose: bool = True):
        gate_name = self.interleaved_gate.name
        if verbose:
            print(f"\n--- Running Full Interleaved {self.num_qubits}-Qubit RB for gate '{gate_name}' ---\n")

        if verbose:
            print("[Step 1/3] Running Standard RB reference experiment...")
        std_experiment = StandardRBExperiment(
            qubits=self.qubits, depths=self.depths, num_sequences=self.num_sequences,
            native_gates=self.native_gates
        )
        results_std = std_experiment.run(engine, shots=shots, plot=False, verbose=verbose)
        if not results_std["fit_successful"]:
            print("Standard RB failed, cannot proceed with Interleaved RB.")
            return None

        if verbose:
            print(f"\n[Step 2/3] Running Interleaved RB experiment with '{gate_name}'...")
        interleaved_experiment = StandardRBExperiment(
            qubits=self.qubits, depths=self.depths, num_sequences=self.num_sequences,
            native_gates=self.native_gates, interleaved_gate=self.interleaved_gate
        )
        results_interleaved = interleaved_experiment.run(engine, shots=shots, plot=False, verbose=verbose)

        if not results_interleaved["fit_successful"]:
            print("Interleaved RB fitting failed.")
            return None
        
        if verbose:
            print("\n[Step 3/3] Analyzing results and calculating EPG...")
        
        epg = calculate_epg(results_std['p'], results_interleaved['p'], self.num_qubits)
        
        print("\n--- Results ---")
        print(f"Calculated Error of gate '{gate_name}' (EPG) = {epg:.3e}")

        if plot:
            if verbose:
                print("Generating comparison plot...")
            fig = plot_rb_comparison(
                results_std, 
                results_interleaved,
                num_qubits=self.num_qubits,
                target_gate_name=gate_name
            )
            fig.show()
        
        return {"epg": epg, "standard_results": results_std, "interleaved_results": results_interleaved}