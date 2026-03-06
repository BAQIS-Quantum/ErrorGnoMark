# =============================================================================
# File    : errorgnomark/experiments/benchmarking/prb.py
# Version : v3.3 - Implements smart default parameters (Corrected & UTF-8 safe)
# Author  : OpenAI-Assistant
# =============================================================================
"""
Purity Randomized Benchmarking (PRB) Experiments

Implements Standard and Interleaved PRB workflows with:
    • Clifford-based sequence generation
    • Optional smart synchronization with baseline results
    • Integrated RB/PRB/Interleaved analysis convergence
    • Optional plot visualization and verbose diagnostic output
"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any

import numpy as np

# ---------------------------------------------------------------------
# Internal Imports
# ---------------------------------------------------------------------
from egm.core.execution.executor import QuantumEngine
from egm.core.circuits.circuit import Gate, QuantumCircuit
from egm.experiments.base import BaseExperiment
from egm.core.circuits.gate_sets import CliffordGateSet, get_gate_set
from egm.analysis.prb import (
    fit_prb_data,
    plot_prb_single,
    plot_prb_comparison,
    calculate_prb_gate_error,
)


# =============================================================================
# Standard Purity RB Experiment
# =============================================================================
class StandardPRBExperiment(BaseExperiment):
    """Controller for standard Purity RB (PRB) experiments."""

    def __init__(
        self,
        qubits: List[int],
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 30,
        gate_set: str = "clifford",
    ):
        super().__init__(qubits)
        self.circuits_per_depth = circuits_per_depth

        # Smart default for depths
        if depths is None:
            if self.num_qubits == 1:
                self.depths = [1, 10, 25, 40, 60, 80, 100]
            else:
                self.depths = [1, 5, 10, 20, 40, 60, 80]
        else:
            self.depths = depths

        resolved_gate_set = get_gate_set(gate_set)
        if not isinstance(resolved_gate_set, CliffordGateSet):
            raise TypeError("Purity RB requires a 'CliffordGateSet'.")

        self.gate_set: CliffordGateSet = resolved_gate_set

        self.metadata = {
            "experiment_type": "StandardPurityBenchmarking",
            "qubits": self.qubits,
            "depths": self.depths,
            "circuits_per_depth": self.circuits_per_depth,
            "gate_set": gate_set,
        }

    # ---------------------------------------------------------------------
    @property
    def circuits(self) -> List[QuantumCircuit]:
        """Purity RB dynamically generates paired circuits."""
        raise NotImplementedError("Purity RB generates circuit pairs dynamically.")

    # ---------------------------------------------------------------------
    def _generate_circuit_pair(
        self, depth: int, seed: Optional[int] = None
    ) -> Tuple[QuantumCircuit, QuantumCircuit]:
        """Generate a pair of PRB circuits (twirled and non-twirled)."""
        master_rng = np.random.RandomState(seed)
        forward_cliffords = []
        inverse_cliffords = []

        for _ in range(depth):
            layer_seed = master_rng.randint(2**32)
            fwd_layer, inv_layer = self.gate_set.get_random_clifford_and_inverse(
                self.qubits, seed=layer_seed
            )
            forward_cliffords.append(fwd_layer)
            inverse_cliffords.append(inv_layer)

        forward_gates = [g for layer in forward_cliffords for g in layer]
        inverse_gates = [g for layer in reversed(inverse_cliffords) for g in layer]

        twirl_seed = master_rng.randint(2**32)
        twirling_gates = self.gate_set.get_random_pauli_layer(
            self.qubits, seed=twirl_seed
        )

        # --- Non-twirled circuit (B) ---
        circuit_b_gates = forward_gates + inverse_gates
        metadata_b = {
            "experiment_type": "StandardPRB",
            "depth": depth,
            "is_twirled_circuit": False,
            "qubits": self.qubits,
            "seed": seed,
        }
        circuit_b = QuantumCircuit(qubits=self.qubits, gates=circuit_b_gates)
        circuit_b.metadata = metadata_b
        circuit_b.measure_all()

        # --- Twirled circuit (A) ---
        circuit_a_gates = circuit_b_gates + twirling_gates
        metadata_a = {
            "experiment_type": "StandardPRB",
            "depth": depth,
            "is_twirled_circuit": True,
            "qubits": self.qubits,
            "seed": seed,
        }
        circuit_a = QuantumCircuit(qubits=self.qubits, gates=circuit_a_gates)
        circuit_a.metadata = metadata_a
        circuit_a.measure_all()

        return circuit_a, circuit_b

    # ---------------------------------------------------------------------
    def run(
        self, engine: QuantumEngine, shots: int = 4096, verbose: bool = False
    ) -> Dict[str, Any]:
        """Execute standard PRB experiment workflow."""
        if verbose:
            print(f"--- Running Standard {self.num_qubits}-Qubit Purity RB ---")

        purities_by_depth = defaultdict(list)
        raw_counts = defaultdict(list)
        total_pairs = len(self.depths) * self.circuits_per_depth

        count = 0
        for depth in self.depths:
            for i in range(self.circuits_per_depth):
                count += 1
                if verbose:
                    print(
                        f"Running circuit pair {count}/{total_pairs} "
                        f"(Depth: {depth})...",
                        end="\r",
                    )

                pair_seed = abs(hash((depth, i, tuple(self.qubits)))) % (2**32)
                circuit_a, circuit_b = self._generate_circuit_pair(depth, seed=pair_seed)

                _, noisy_counts_a = engine.run(circuit_a, shots)
                _, noisy_counts_b = engine.run(circuit_b, shots)

                raw_counts[depth].append(
                    {"twirled": noisy_counts_a, "non_twirled": noisy_counts_b}
                )

                total_shots_a = sum(noisy_counts_a.values())
                total_shots_b = sum(noisy_counts_b.values())

                purity = float("nan")
                if total_shots_a > 0 and total_shots_b > 0:
                    prob_a = noisy_counts_a.get("0" * self.num_qubits, 0) / total_shots_a
                    prob_b = noisy_counts_b.get("0" * self.num_qubits, 0) / total_shots_b
                    purity = 2 * prob_a - prob_b

                if not np.isnan(purity):
                    purities_by_depth[depth].append(purity)

        if verbose:
            print("\nExperiment run complete.")

        return {
            "metadata": self.metadata,
            "purities_by_depth": dict(purities_by_depth),
            "raw_counts": dict(raw_counts),
        }

    # ---------------------------------------------------------------------
    def analyze_results(self, results: Dict, plot: bool = True) -> Dict[str, Any]:
        """Analyze Purity RB results."""
        print("\n--- Analyzing Standard PRB Results ---")

        purities_by_depth = results["purities_by_depth"]
        print("Fitting standard Purity RB data...")
        fit_results = fit_prb_data(purities_by_depth, self.num_qubits)

        if fit_results.get("fit_successful"):
            print(f"Fit successful. Purity Alpha = {fit_results['alpha']:.3e}")
        else:
            print("Fit failed.")

        if plot:
            print("Generating plot...")
            plot_prb_single(fit_results, self.num_qubits)

        return fit_results


# =============================================================================
# Interleaved Purity RB Experiment
# =============================================================================
class InterleavedPRBExperiment(StandardPRBExperiment):
    """Controller for Interleaved PRB experiment with smart default synchronization."""

    def __init__(
        self,
        qubits: List[int],
        target_gate_name: str,
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = 30,
        gate_set: str = "clifford",
    ):
        super().__init__(qubits, depths, circuits_per_depth, gate_set)
        self.target_gate_name = target_gate_name.upper()

        if self.target_gate_name == "CNOT" and self.num_qubits == 2:
            target_qubits = tuple(self.qubits)
        elif self.num_qubits == 1:
            target_qubits = (self.qubits[0],)
        else:
            target_qubits = tuple(self.qubits)

        self.target_gate = Gate(name=self.target_gate_name, qubits=target_qubits)
        if len(self.target_gate.qubits) != self.num_qubits:
            raise ValueError(
                f"Target gate '{self.target_gate_name}' acts on "
                f"{len(self.target_gate.qubits)} qubits, "
                f"but experiment is for {self.num_qubits}."
            )

        # Update metadata
        self.metadata.update(
            {
                "experiment_type": "InterleavedPurityBenchmarking",
                "interleaved_gate": self.target_gate_name,
                "depths": self.depths,
            }
        )

    # ---------------------------------------------------------------------
    def _generate_circuit_pair(
        self, depth: int, seed: Optional[int] = None
    ) -> Tuple[QuantumCircuit, QuantumCircuit]:
        """Generate interleaved PRB circuit pair."""
        master_rng = np.random.RandomState(seed)
        op_pairs = []
        for _ in range(depth):
            layer_seed = master_rng.randint(2**32)
            fwd_cliff, inv_cliff = self.gate_set.get_random_clifford_and_inverse(
                self.qubits, seed=layer_seed
            )
            step_fwd = fwd_cliff + [self.target_gate]
            step_inv = [self.target_gate.inverse()] + inv_cliff
            op_pairs.append((step_fwd, step_inv))

        forward_gates = [g for fwd, _ in op_pairs for g in fwd]
        inverse_gates = [g for _, inv in reversed(op_pairs) for g in inv]

        twirl_seed = master_rng.randint(2**32)
        twirling_gates = self.gate_set.get_random_pauli_layer(
            self.qubits, seed=twirl_seed
        )

        # --- Non-twirled circuit (B) ---
        circuit_b_gates = forward_gates + inverse_gates
        metadata_b = {
            "experiment_type": "InterleavedPRB",
            "depth": depth,
            "interleaved_gate_name": self.target_gate_name,
            "is_twirled_circuit": False,
            "qubits": self.qubits,
            "seed": seed,
        }
        circuit_b = QuantumCircuit(qubits=self.qubits, gates=circuit_b_gates)
        circuit_b.metadata = metadata_b
        circuit_b.measure_all()

        # --- Twirled circuit (A) ---
        circuit_a_gates = circuit_b_gates + twirling_gates
        metadata_a = {
            "experiment_type": "InterleavedPRB",
            "depth": depth,
            "interleaved_gate_name": self.target_gate_name,
            "is_twirled_circuit": True,
            "qubits": self.qubits,
            "seed": seed,
        }
        circuit_a = QuantumCircuit(qubits=self.qubits, gates=circuit_a_gates)
        circuit_a.metadata = metadata_a
        circuit_a.measure_all()

        return circuit_a, circuit_b

    # ---------------------------------------------------------------------
    def run(
        self,
        engine: QuantumEngine,
        shots: int = 4096,
        standard_results: Optional[Dict] = None,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Execute Interleaved PRB experiment with optional baseline synchronization."""
        # Synchronize with baseline if provided
        if standard_results:
            if verbose:
                print("\n[Phase 1/2] Using provided Standard PRB results as baseline.")
            baseline_depths = standard_results.get("metadata", {}).get("depths")
            if baseline_depths and self.depths != baseline_depths:
                if verbose:
                    print(
                        f"INFO: Overriding interleaved depths to match baseline depths: "
                        f"{baseline_depths}"
                    )
                self.depths = baseline_depths
                self.metadata["depths"] = self.depths

        # If no baseline, run a new standard experiment
        if standard_results is None:
            if verbose:
                print("\n[Phase 1/2] Standard PRB results not provided. Running baseline...")
            gate_set_name = getattr(self.gate_set, "name", "clifford")
            std_exp = StandardPRBExperiment(
                self.qubits, self.depths, self.circuits_per_depth, gate_set_name
            )
            standard_results = std_exp.run(engine, shots, verbose)

        if verbose:
            print(f"\n[Phase 2/2] Running Interleaved Purity RB with '{self.target_gate_name}'...")

        interleaved_results = super().run(engine, shots, verbose)

        return {
            "standard_run_results": standard_results,
            "interleaved_run_results": interleaved_results,
        }

    # ---------------------------------------------------------------------
    def analyze_results(self, results: Dict, plot: bool = True) -> Dict[str, Any]:
        """Analyze Interleaved PRB results and calculate gate error."""
        print(
            f"\n--- Analyzing Interleaved PRB Results for Gate '{self.target_gate_name}' ---"
        )

        standard_run_results = results["standard_run_results"]
        interleaved_run_results = results["interleaved_run_results"]

        print("\nAnalyzing baseline (Standard PRB) data...")
        std_analysis = super().analyze_results(standard_run_results, plot=False)

        print("\nAnalyzing interleaved data...")
        int_analysis = super().analyze_results(interleaved_run_results, plot=False)

        print("\nCalculating interleaved gate error...")
        gate_error_results = calculate_prb_gate_error(
            std_analysis, int_analysis, num_qubits=self.num_qubits
        )

        if gate_error_results.get("calculation_successful"):
            print(
                f"  > Estimated Error per Gate ('{self.target_gate_name}'): "
                f"{gate_error_results['gate_error']:.3e}"
            )
        else:
            print("  > Gate error calculation failed.")

        if plot:
            print("Generating comparison plot...")
            plot_prb_comparison(
                std_analysis, int_analysis, self.num_qubits, self.target_gate_name
            )

        return {
            "interleaved_gate_error_analysis": gate_error_results,
            "standard_fit_analysis": std_analysis,
            "interleaved_fit_analysis": int_analysis,
        }

# =============================================================================
# End of File
# =============================================================================