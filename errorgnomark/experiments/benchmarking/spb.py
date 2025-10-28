# File Path: errorgnomark/experiments/benchmarking/spb.py
#
# [COMPATIBILITY UPDATE v3.0 - Aligned with XEBExperiment interface]
# Description: This module defines the experiment classes for performing Speckle Purity
# Benchmarking (SPB) and Interleaved SPB. It handles circuit generation, execution via a
# QuantumEngine, and orchestration of the analysis by calling functions from the
# errorgnomark.analysis.spb module.

import numpy as np
from collections import defaultdict
from typing import List, Dict, Optional, Any

from errorgnomark.engine import QuantumEngine
from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.experiments.base import BaseExperiment
from errorgnomark.circuits.gate_sets import CliffordGateSet, get_gate_set
# Imports from the analysis module are now aligned with the compatible API.
from errorgnomark.analysis.spb import (
    _calculate_purity_from_counts,
    fit_spb_data,
    plot_spb_decay,
    plot_spb_comparison,
    calculate_spb_gate_error
)

class SPBExperiment(BaseExperiment):
    """
    Performs a standard Speckle Purity Benchmarking (SPB) experiment.

    SPB characterizes the average fidelity of a set of gates by measuring the decay
    of "speckle purity" as a function of circuit depth. It involves running random
    circuits composed of gates from a specified gate set (typically Clifford gates).
    """
    def __init__(
        self,
        qubits: List[int],
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 30,
        gate_set: str = "clifford"
    ):
        """
        Initializes the SPB experiment parameters.

        Args:
            qubits (List[int]): The list of qubits to run the experiment on.
            depths (Optional[List[int]]): A list of circuit depths (number of Clifford layers)
                to test. If None, sensible defaults are chosen based on qubit count.
            circuits_per_depth (int): The number of random circuits to generate and run
                for each depth to ensure good statistical sampling.
            gate_set (str): The name of the gate set to use for generating random circuits.
                Must resolve to a CliffordGateSet.
        """
        super().__init__(qubits)
        # Provide sensible default depths if none are specified by the user.
        if depths is None:
            self.depths = list(range(5, 101, 10)) if self.num_qubits == 1 else list(range(4, 41, 4))
        else:
            self.depths = depths
        self.circuits_per_depth = circuits_per_depth
        
        # Ensure the specified gate set is a valid Clifford gate set, as required by SPB.
        resolved_gate_set = get_gate_set(gate_set)
        if not isinstance(resolved_gate_set, CliffordGateSet):
            raise TypeError("SPB requires a 'CliffordGateSet'.")
        self.gate_set: CliffordGateSet = resolved_gate_set
        
        # Internal cache for generated circuits.
        self._circuits: List[QuantumCircuit] = []
        # Dictionary to store the final analysis results.
        self.results: Dict = {}

    def _generate_circuits(self):
        """Generates all random circuits for the standard SPB experiment."""
        self._circuits = []
        for depth in self.depths:
            for i in range(self.circuits_per_depth):
                circuit = QuantumCircuit(self.qubits)
                # Metadata is crucial for organizing results later.
                circuit.metadata = {'depth': depth, 'circuit_index': i, 'type': 'standard'}
                # A standard SPB circuit consists of 'depth' layers of random Clifford gates.
                for _ in range(depth):
                    clifford_layer, _ = self.gate_set.get_random_clifford_and_inverse(self.qubits)
                    circuit.add_gates(clifford_layer)
                circuit.measure_all()
                self._circuits.append(circuit)

    @property
    def circuits(self) -> List[QuantumCircuit]:
        """
        Lazily generates and returns the list of experiment circuits.
        The circuits are generated only on the first access to this property.
        """
        if not self._circuits:
            self._generate_circuits()
        return self._circuits

    def run(self, engine: QuantumEngine, shots: int = 2000, verbose: bool = False, plot: bool = False) -> Dict:
        """
        Executes the SPB experiment, analyzes the data, and returns the results.

        Args:
            engine (QuantumEngine): The quantum execution backend.
            shots (int): The number of measurement shots per circuit.
            verbose (bool): If True, prints progress updates to the console.
            plot (bool): If True, generates and displays a plot of the results.

        Returns:
            Dict: A dictionary containing the full analysis results, including fit parameters and raw data.
        """
        if verbose: print(f"--- Running Standard {self.num_qubits}-Qubit SPB ---")
        
        # Step 1: Run circuits and collect purity data, grouped by depth.
        purities_by_depth = defaultdict(list)
        for i, circuit in enumerate(self.circuits):
            if verbose: print(f"\rRunning circuit {i+1}/{len(self.circuits)}...", end='')
            _, counts = engine.run(circuit, shots)
            purity = _calculate_purity_from_counts(counts, shots)
            if not np.isnan(purity):
                purities_by_depth[circuit.metadata['depth']].append(purity)
        
        # Step 2: Fit the aggregated purity data to an exponential decay model.
        if verbose: print("\nFitting SPB data...")
        self.results = fit_spb_data(purities_by_depth, self.num_qubits)
        
        if verbose and self.results.get('fit_successful'):
            p_c = self.results.get('fit_results', {}).get('p_c', 0)
            print(f"Fit successful. p_c = {p_c:.5f}")
        elif verbose:
            print("Fit failed.")

        # Step 3: Optionally plot the results.
        if plot and self.results.get('fit_successful'):
            # This call now matches the compatible API of the analysis module.
            plot_spb_decay(
                raw_data=self.results['raw_data'],
                fit_results=self.results['fit_results'],
                title=f"{self.num_qubits}-Qubit Standard SPB"
            )
            
        return self.results

class InterleavedSPBExperiment(SPBExperiment):
    """
    Performs an Interleaved SPB experiment to find the error of a specific target gate.

    This experiment is similar to standard SPB, but a specific `target_gate` is
    interleaved (inserted) between each random Clifford layer. By comparing the
    purity decay of this interleaved experiment to a standard SPB experiment, the
    error associated with the target gate can be isolated and quantified.
    """
    def __init__(
        self,
        qubits: List[int],
        target_gate_name: str,
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 30
    ):
        """
        Initializes the Interleaved SPB experiment.

        Args:
            qubits (List[int]): The qubits involved.
            target_gate_name (str): The name of the gate whose error is to be measured.
            depths (Optional[List[int]]): List of circuit depths.
            circuits_per_depth (int): Number of random circuits per depth.
        """
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
                # An interleaved circuit consists of 'depth' layers of (Clifford + Target Gate).
                for _ in range(depth):
                    clifford_layer, _ = self.gate_set.get_random_clifford_and_inverse(self.qubits)
                    circuit.add_gates(clifford_layer)
                    # The target gate is inserted here.
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
        """
        Executes the full interleaved SPB workflow.

        This involves two phases:
        1. Obtaining baseline data from a standard SPB run.
        2. Running the interleaved SPB experiment.
        The results are then compared to calculate the target gate's error.

        Args:
            engine (QuantumEngine): The quantum execution backend.
            shots (int): Number of shots per circuit.
            standard_results (Optional[Dict]): If provided, these pre-computed standard SPB
                results are used as the baseline, saving execution time. If None, a new
                standard SPB experiment is run automatically.
            verbose (bool): If True, prints progress updates.
            plot (bool): If True, generates a comparison plot.

        Returns:
            Dict[str, Any]: A dictionary containing the gate error calculation, along with the
                            full results from both the standard and interleaved runs.
        """
        # Phase 1: Obtain baseline results from a standard SPB experiment.
        if standard_results is None:
            # If no baseline is provided, run a standard SPB experiment first.
            if verbose: print("[Phase 1/2] Running Standard SPB for baseline...")
            std_exp = SPBExperiment(self.qubits, self.depths, self.circuits_per_depth)
            results_std = std_exp.run(engine, shots, verbose=verbose, plot=False)
        else:
            # Use the pre-computed baseline results.
            if verbose: print("[Phase 1/2] Using provided Standard SPB results for baseline.")
            results_std = standard_results
        
        # Phase 2: Run the interleaved experiment. This reuses the parent `run` method
        # but with the interleaved circuits generated by this class.
        if verbose: print(f"\n[Phase 2/2] Running Interleaved SPB with '{self.target_gate_name}'...")
        results_int = super().run(engine, shots, verbose=verbose, plot=False)

        # Phase 3: Analyze the combined data to extract the gate error.
        if verbose: print("\nAnalyzing data...")
        gate_error_results = calculate_spb_gate_error(results_std, results_int, self.num_qubits)

        # Report the final calculated results.
        if verbose and gate_error_results.get('calculation_successful'):
            p_c_std = results_std.get('fit_results', {}).get('p_c')
            p_c_int = results_int.get('fit_results', {}).get('p_c')
            print("\n--- Results ---")
            print(f"Standard p_c: {p_c_std:.5f}, Interleaved p_c: {p_c_int:.5f}")
            print(f"Gate Purity (p_G): {gate_error_results.get('p_G'):.5f}")
            print(f"Error of gate '{self.target_gate_name}' (r_G) = {gate_error_results.get('gate_error'):.3e}")
        elif verbose:
            print("\nCould not calculate gate error: " + gate_error_results.get('reason', 'Unknown reason.'))
        
        # Optionally generate a plot comparing the standard and interleaved decays.
        if plot:
            if verbose: print("Generating comparison plot...")
            plot_spb_comparison(results_std, results_int, self.num_qubits, self.target_gate_name)

        # Package all results into a single comprehensive dictionary for the user.
        final_results = {**gate_error_results, 'standard_results': results_std, 'interleaved_results': results_int}
        return final_results