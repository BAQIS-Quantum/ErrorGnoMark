# # File: errorgnomark/experiments/benchmarking/rb.py
# # ---------------------------------------------------------------------
# # Module: Randomized Benchmarking (RB) Experiment Definitions
# # ---------------------------------------------------------------------
# # This module defines the base classes for performing Standard
# # and Interleaved Randomized Benchmarking experiments within the
# # ErrorGnoMark framework.
# #
# # It supports:
# #   - Circuit generation using a configurable Clifford factory.
# #   - Data aggregation and survival probability computation.
# #   - Automated RB fitting through the analysis module.
# #   - Optional visualization of fitted RB decay curves.
# # ---------------------------------------------------------------------

# from __future__ import annotations
# import numpy as np
# import random
# import logging
# from typing import List, Dict, Optional, Union, Tuple, Protocol, Any, NamedTuple
# import matplotlib.pyplot as plt

# # ---------------------------------------------------------------------
# # Internal Framework Imports
# # ---------------------------------------------------------------------
# from egm.core.circuits.circuit import QuantumCircuit, Gate
# from egm.core.engine.executor import QuantumEngine
# from egm.core.analysis.rb import fit_rb_data, calculate_epg
# from egm.reporting.visualizers.rb_plotter import plot_rb_data as plot_rb_single
# from egm.reporting.visualizers.rb_plotter import plot_rb_comparison
# from egm.core.circuits.gate_sets import CliffordGateSet

# # ---------------------------------------------------------------------
# # Logging Configuration
# # ---------------------------------------------------------------------
# logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# # ---------------------------------------------------------------------
# # Default Parameter Values
# # ---------------------------------------------------------------------
# DEFAULT_RB_DEPTHS: List[int] = [1, 10, 20, 40, 60, 80, 100, 125]
# DEFAULT_CIRCUITS_PER_DEPTH: int = 25
# EXAMPLE_NATIVE_GATES: List[str] = ["cz", "sx", "rz", "h", "s"]

# # ---------------------------------------------------------------------
# # Protocols and Data Containers
# # ---------------------------------------------------------------------
# class CliffordFactory(Protocol):
#     """Interface for generating random Clifford sequences."""

#     def get_random_clifford_and_inverse(
#         self, qubits: List[int], seed: Optional[Union[int, float]]
#     ) -> Tuple[List[Gate], List[Gate]]:
#         ...


# class AggregatedRBData(NamedTuple):
#     """Aggregated statistics for RB survival probabilities."""

#     depths: List[int]
#     means: List[float]
#     stds: List[float]


# # ---------------------------------------------------------------------
# # Standard Randomized Benchmarking Experiment
# # ---------------------------------------------------------------------
# class StandardRBExperiment:
#     """Implements a standard Clifford-based Randomized Benchmarking protocol."""

#     def __init__(
#         self,
#         qubits: Union[int, List[int]],
#         depths: List[int] = DEFAULT_RB_DEPTHS,
#         circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
#         native_gates: Optional[List[str]] = None,
#         seed: Optional[Union[int, float]] = None,
#         clifford_factory: Optional[CliffordFactory] = None,
#     ):
#         self.qubits = [qubits] if isinstance(qubits, int) else qubits
#         self.num_qubits = len(self.qubits)
#         self.depths = sorted(set(depths))
#         self.circuits_per_depth = circuits_per_depth
#         self.native_gates = native_gates
#         self.seed = seed
#         self.clifford_factory = clifford_factory or CliffordGateSet()
#         self.results: Optional[Dict[str, Any]] = None

#         if self.native_gates:
#             logging.info(
#                 f"RB experiment configured for PHYSICAL representation. "
#                 f"Using native gates: {self.native_gates}"
#             )
#         else:
#             logging.info(
#                 "RB experiment configured for LOGICAL representation (no gate decomposition)."
#             )

#     # -----------------------------------------------------------------
#     # Circuit Generation
#     # -----------------------------------------------------------------
#     def _generate_circuit(
#         self,
#         depth: int,
#         seed: Optional[Union[int, float]],
#         interleaved_gate: Optional[Gate] = None,
#     ) -> QuantumCircuit:
#         """Generate a single randomized benchmarking circuit."""

#         rng = random.Random(seed)
#         circuit = QuantumCircuit(qubits=self.qubits)
#         inverse_gate_sequences = []

#         for _ in range(depth):
#             fwd_gates, inv_gates = self.clifford_factory.get_random_clifford_and_inverse(
#                 self.qubits, seed=rng.random()
#             )
#             circuit.add_gates(fwd_gates)
#             if interleaved_gate:
#                 circuit.add_gate(interleaved_gate)
#             inverse_gate_sequences.append(inv_gates)

#         # Append inverses in reverse order to invert total sequence
#         for inv_gates in reversed(inverse_gate_sequences):
#             circuit.add_gates(inv_gates)

#         circuit.measure_all()
#         circuit.metadata["depth"] = depth
#         circuit.metadata["seed"] = seed
#         if interleaved_gate:
#             circuit.metadata["interleaved_gate_name"] = interleaved_gate.name

#         return circuit

#     def generate_single_circuit(
#         self, depth: int, seed: Optional[Union[int, float]] = None
#     ) -> QuantumCircuit:
#         """Create a single RB circuit at the specified depth."""
#         interleaved_gate = getattr(self, "interleaved_gate", None)
#         circuit = self._generate_circuit(depth, seed, interleaved_gate=interleaved_gate)
#         if self.native_gates:
#             circuit = circuit.decompose(basis_gates=self.native_gates)
#         return circuit

#     def circuits(self) -> List[QuantumCircuit]:
#         """Generate all RB circuits for this experiment."""
#         all_circuits: List[QuantumCircuit] = []
#         main_rng = random.Random(self.seed)

#         for depth in self.depths:
#             for i in range(self.circuits_per_depth):
#                 circuit_seed = main_rng.random()
#                 circuit = self.generate_single_circuit(depth, circuit_seed)
#                 circuit.metadata["sample_idx"] = i
#                 all_circuits.append(circuit)

#         return all_circuits

#     # -----------------------------------------------------------------
#     # Aggregation
#     # -----------------------------------------------------------------
#     def _aggregate_results(
#         self,
#         raw_results: List[Tuple[Dict[str, float], Dict[str, int]]],
#         circuits: List[QuantumCircuit],
#         shots: int,
#     ) -> AggregatedRBData:
#         """Aggregate raw counts into average survival probabilities per depth."""
#         survivals_by_depth = {d: [] for d in self.depths}
#         ground_state_str = "0" * self.num_qubits

#         for i, circuit in enumerate(circuits):
#             depth = circuit.metadata["depth"]
#             _, noisy_counts = raw_results[i]
#             survival_prob = noisy_counts.get(ground_state_str, 0) / shots
#             survivals_by_depth[depth].append(survival_prob)

#         agg_depths, agg_means, agg_stds = [], [], []
#         for depth in self.depths:
#             survs = survivals_by_depth[depth]
#             agg_depths.append(depth)
#             agg_means.append(np.mean(survs))
#             # Standard error of the mean
#             agg_stds.append(np.std(survs, ddof=1) / np.sqrt(len(survs)))

#         return AggregatedRBData(
#             depths=agg_depths, means=agg_means, stds=agg_stds
#         )

#     # -----------------------------------------------------------------
#     # Execution Workflow
#     # -----------------------------------------------------------------
#     def run(
#         self,
#         engine: QuantumEngine,
#         shots: int,
#         plot: bool = True,
#         axes: Optional[plt.Axes] = None,
#     ) -> Dict[str, Any]:
#         """Execute the full RB workflow: circuit generation, execution, fitting, and plot."""
#         rb_type = (
#             "Interleaved" if isinstance(self, InterleavedRBExperiment) else "Standard"
#         )
#         logging.info(f"--- Running {rb_type} {self.num_qubits}-Qubit RB ---")

#         # 1. Generate circuits
#         circuits = self.circuits()
#         logging.info(f"[1/4] Generated {len(circuits)} circuits for {len(self.depths)} depths.")

#         # 2. Execute circuits
#         logging.info(f"[2/4] Executing circuits on backend ({shots} shots each)...")
#         raw_results = engine.execute_with_ideal(circuits, shots=shots)

#         # 3. Aggregate measurement results
#         logging.info("[3/4] Aggregating survival probabilities...")
#         agg_data = self._aggregate_results(raw_results, circuits, shots)

#         # 4. Fit RB decay curve
#         logging.info("[4/4] Performing RB fitting...")
#         fit_results = fit_rb_data(
#             depths=agg_data.depths,
#             means=agg_data.means,
#             stds=agg_data.stds,
#             num_qubits=self.num_qubits,
#         )
#         self.results = fit_results

#         if fit_results.get("fit_successful"):
#             logging.info(f"Fit successful. EPC = {fit_results['epc']:.3e}")
#         else:
#             logging.warning("RB fitting unsuccessful.")

#         # Visualization
#         if plot:
#             show_plot_at_end = axes is None
#             if fit_results.get("fit_successful"):
#                 current_ax = axes or plt.subplots(figsize=(8, 5))[1]
#                 title = f"{rb_type} {self.num_qubits}-Qubit RB Decay"
#                 plot_rb_single(fit_results, title=title, ax=current_ax)
#                 if show_plot_at_end:
#                     plt.tight_layout()
#                     plt.show()
#             else:
#                 logging.warning("Skipping plot generation (fit failed).")

#         return fit_results

#     def aggregate(self, raw_results, shots: int) -> Dict[str, List[float]]:
#         """Public wrapper around `_aggregate_results()` for manual workflows."""
#         circuits = self.circuits()
#         agg_data = self._aggregate_results(raw_results, circuits, shots)
#         return {"depths": agg_data.depths, "means": agg_data.means, "stds": agg_data.stds}


# # ---------------------------------------------------------------------
# # Interleaved Randomized Benchmarking Experiment
# # ---------------------------------------------------------------------
# class InterleavedRBExperiment(StandardRBExperiment):
#     """Perform Interleaved RB to extract gate-specific error probabilities."""

#     def __init__(
#         self,
#         qubits: Union[int, List[int]],
#         interleaved_gate: Gate,
#         depths: List[int] = DEFAULT_RB_DEPTHS,
#         circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
#         native_gates: Optional[List[str]] = None,
#         seed: Optional[Union[int, float]] = None,
#         clifford_factory: Optional[CliffordFactory] = None,
#     ):
#         super().__init__(
#             qubits=qubits,
#             depths=depths,
#             circuits_per_depth=circuits_per_depth,
#             native_gates=native_gates,
#             seed=seed,
#             clifford_factory=clifford_factory,
#         )
#         self.interleaved_gate = interleaved_gate

#     def run(
#         self,
#         engine: QuantumEngine,
#         shots: int,
#         plot: bool = True,
#         axes: Optional[plt.Axes] = None,
#     ) -> Optional[Dict[str, Any]]:
#         """Execute the full Interleaved RB workflow including EPG extraction."""
#         gate_name = self.interleaved_gate.name.upper()
#         logging.info(
#             f"\n--- Running Interleaved {self.num_qubits}-Qubit RB for Gate '{gate_name}' ---"
#         )

#         # Step 1: Standard RB Reference
#         logging.info("[1/3] Running standard reference RB ...")
#         std_rb = StandardRBExperiment(
#             qubits=self.qubits,
#             depths=self.depths,
#             circuits_per_depth=self.circuits_per_depth,
#             native_gates=self.native_gates,
#             seed=self.seed,
#             clifford_factory=self.clifford_factory,
#         )
#         results_std = std_rb.run(engine, shots, plot=False)
#         if not results_std.get("fit_successful"):
#             logging.error("Reference fit failed; aborting Interleaved RB.")
#             return None
#         logging.info(f"Reference fit successful. EPC = {results_std['epc']:.3e}")

#         # Step 2: Interleaved RB
#         logging.info(f"[2/3] Running Interleaved RB with gate '{gate_name}' ...")
#         results_irb = super().run(engine, shots=shots, plot=False)
#         if not results_irb.get("fit_successful"):
#             logging.error("Interleaved RB fit failed.")
#             return None

#         # Step 3: Calculate Error per Gate (EPG)
#         logging.info("[3/3] Calculating Error Per Gate (EPG) ...")
#         epg = calculate_epg(results_std["p"], results_irb["p"], self.num_qubits)

#         logging.info(f"Reference EPC = {results_std['epc']:.3e}")
#         logging.info(f"Interleaved EPC = {results_irb['epc']:.3e}")
#         logging.info(f"Derived Gate EPG ({gate_name}) = {epg:.3e}")

#         results_irb["epg"] = epg

#         # Visualization
#         if plot:
#             show_plot_at_end = axes is None
#             current_ax = axes or plt.subplots(figsize=(8, 5))[1]
#             plot_rb_comparison(results_std, results_irb, target_gate_name=gate_name, ax=current_ax)
#             if show_plot_at_end:
#                 plt.tight_layout()
#                 plt.show()

#         self.results = {
#             "epg": epg,
#             "standard_results": results_std,
#             "interleaved_results": results_irb,
#         }
#         return self.results


# File: errorgnomark/experiments/benchmarking/rb.py
# ---------------------------------------------------------------------
# Module: Randomized Benchmarking (RB) Experiment Definitions
# ---------------------------------------------------------------------
# This module defines the base classes for performing Standard
# and Interleaved Randomized Benchmarking experiments within the
# ErrorGnoMark framework.
#
# It supports:
#   - Circuit generation using a configurable Clifford factory.
#   - Data aggregation and survival probability computation.
#   - Automated RB fitting through the analysis module.
#   - Optional visualization of fitted RB decay curves.
#   - Dual-mode execution: QuantumEngine simulation & user-provided
#     experimental data ingestion.
# ---------------------------------------------------------------------

from __future__ import annotations
import numpy as np
import random
import logging
from typing import List, Dict, Optional, Union, Tuple, Protocol, Any, NamedTuple
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Internal Framework Imports
# ---------------------------------------------------------------------
from egm.core.circuits.circuit import QuantumCircuit, Gate
from egm.core.engine.executor import QuantumEngine
from egm.core.analysis.rb import fit_rb_data, calculate_epg
from egm.reporting.visualizers.rb_plotter import plot_rb_data as plot_rb_single
from egm.reporting.visualizers.rb_plotter import plot_rb_comparison
from egm.core.circuits.gate_sets import CliffordGateSet

# ---------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# ---------------------------------------------------------------------
# Default Parameter Values
# ---------------------------------------------------------------------
DEFAULT_RB_DEPTHS: List[int] = [0, 1, 10, 20, 40, 60, 80, 100, 125]
DEFAULT_CIRCUITS_PER_DEPTH: int = 25
EXAMPLE_NATIVE_GATES: List[str] = ["cz", "sx", "rz", "h", "s"]

# ---------------------------------------------------------------------
# Protocols and Data Containers
# ---------------------------------------------------------------------
class CliffordFactory(Protocol):
    """Interface for generating random Clifford sequences."""

    def get_random_clifford_and_inverse(
        self, qubits: List[int], seed: Optional[Union[int, float]]
    ) -> Tuple[List[Gate], List[Gate]]:
        ...


class AggregatedRBData(NamedTuple):
    """Aggregated statistics for RB survival probabilities."""

    depths: List[int]
    means: List[float]
    stds: List[float]


# ---------------------------------------------------------------------
# Standard Randomized Benchmarking Experiment
# ---------------------------------------------------------------------
class StandardRBExperiment:
    """Implements a standard Clifford-based Randomized Benchmarking protocol."""

    def __init__(
        self,
        qubits: Union[int, List[int]],
        depths: List[int] = DEFAULT_RB_DEPTHS,
        circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
        native_gates: Optional[List[str]] = None,
        seed: Optional[Union[int, float]] = None,
        clifford_factory: Optional[CliffordFactory] = None,
    ):
        self.qubits = [qubits] if isinstance(qubits, int) else qubits
        self.num_qubits = len(self.qubits)
        self.depths = sorted(set(depths))
        self.circuits_per_depth = circuits_per_depth
        self.native_gates = native_gates
        self.seed = seed
        self.clifford_factory = clifford_factory or CliffordGateSet()
        self.results: Optional[Dict[str, Any]] = None

        if self.native_gates:
            logging.info(
                f"RB experiment configured for PHYSICAL representation. "
                f"Using native gates: {self.native_gates}"
            )
        else:
            logging.info(
                "RB experiment configured for LOGICAL representation (no gate decomposition)."
            )

    # -----------------------------------------------------------------
    # Circuit Generation
    # -----------------------------------------------------------------
    def _generate_circuit(
        self,
        depth: int,
        seed: Optional[Union[int, float]],
        interleaved_gate: Optional[Gate] = None,
    ) -> QuantumCircuit:
        """Generate a single randomized benchmarking circuit."""

        rng = random.Random(seed)
        circuit = QuantumCircuit(qubits=self.qubits)
        inverse_gate_sequences = []

        for _ in range(depth):
            fwd_gates, inv_gates = self.clifford_factory.get_random_clifford_and_inverse(
                self.qubits, seed=rng.random()
            )
            circuit.add_gates(fwd_gates)
            if interleaved_gate:
                circuit.add_gate(interleaved_gate)
            inverse_gate_sequences.append(inv_gates)

        # Append inverses in reverse order to invert total sequence
        for inv_gates in reversed(inverse_gate_sequences):
            circuit.add_gates(inv_gates)

        circuit.measure_all()
        circuit.metadata["depth"] = depth
        circuit.metadata["seed"] = seed
        if interleaved_gate:
            circuit.metadata["interleaved_gate_name"] = interleaved_gate.name

        return circuit

    def generate_single_circuit(
        self, depth: int, seed: Optional[Union[int, float]] = None
    ) -> QuantumCircuit:
        """Create a single RB circuit at the specified depth."""
        interleaved_gate = getattr(self, "interleaved_gate", None)
        circuit = self._generate_circuit(depth, seed, interleaved_gate=interleaved_gate)
        if self.native_gates:
            circuit = circuit.decompose(basis_gates=self.native_gates)
        return circuit

    def circuits(self) -> List[QuantumCircuit]:
        """Generate all RB circuits for this experiment."""
        all_circuits: List[QuantumCircuit] = []
        main_rng = random.Random(self.seed)
        for depth in self.depths:
            for i in range(self.circuits_per_depth):
                circuit_seed = main_rng.random()
                if depth == 0:
                    circuit = QuantumCircuit(qubits=self.qubits)
                    circuit.measure_all()
                    circuit.metadata["depth"] = 0
                    circuit.metadata["seed"] = circuit_seed
                else:
                    circuit = self.generate_single_circuit(depth, circuit_seed)
                circuit.metadata["sample_idx"] = i
                all_circuits.append(circuit)
        return all_circuits

    # -----------------------------------------------------------------
    # Aggregation
    # -----------------------------------------------------------------
    def _aggregate_results(
        self,
        raw_results: List[Tuple[Dict[str, float], Dict[str, int]]],
        circuits: List[QuantumCircuit],
        shots: int,
    ) -> AggregatedRBData:
        """Aggregate raw counts into average survival probabilities per depth."""
        survivals_by_depth = {d: [] for d in self.depths}
        ground_state_str = "0" * self.num_qubits

        for i, circuit in enumerate(circuits):
            depth = circuit.metadata["depth"]
            _, noisy_counts = raw_results[i]
            survival_prob = noisy_counts.get(ground_state_str, 0) / shots
            survivals_by_depth[depth].append(survival_prob)

        agg_depths, agg_means, agg_stds = [], [], []
        for depth in self.depths:
            survs = survivals_by_depth[depth]
            agg_depths.append(depth)
            agg_means.append(np.mean(survs))
            agg_stds.append(np.std(survs, ddof=1) / np.sqrt(len(survs)))

        return AggregatedRBData(depths=agg_depths, means=agg_means, stds=agg_stds)

    # -----------------------------------------------------------------
    # Execution Workflow (Enhanced Dual-Mode)
    # -----------------------------------------------------------------
    def run(
        self,
        engine: Optional[QuantumEngine] = None,
        shots: Optional[int] = None,
        plot: bool = True,
        axes: Optional[plt.Axes] = None,
        experimental_results: Optional[List[Tuple[Dict[str, float], Dict[str, int]]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the RB workflow in either Engine Simulated mode or User Data mode.
        """
        rb_type = (
            "Interleaved" if isinstance(self, InterleavedRBExperiment) else "Standard"
        )
        mode = "User Data" if experimental_results is not None else "Engine"
        logging.info(f"--- Running {rb_type} {self.num_qubits}-Qubit RB [{mode} Mode] ---")

        # Step 1: Circuit Generation
        circuits = self.circuits()
        logging.info(f"[1/4] Prepared {len(circuits)} circuits for {len(self.depths)} depths.")

        # Step 2: Data Source (Engine or User)
        if experimental_results is None:
            if engine is None:
                raise ValueError("QuantumEngine must be provided in Engine mode.")
            if shots is None:
                raise ValueError("Shots must be specified in Engine mode.")
            logging.info(f"[2/4] Executing on backend ({shots} shots per circuit)...")
            raw_results = engine.execute_with_ideal(circuits, shots=shots)
        else:
            logging.info("[2/4] Using user-provided experimental measurement data.")
            raw_results = experimental_results
            if shots is None and len(raw_results) > 0:
                first_counts = raw_results[0][1]
                shots = sum(first_counts.values())
                logging.info(f"Inferred shots = {shots}")

        if len(raw_results) != len(circuits):
            logging.warning(
                f"Result length mismatch: {len(raw_results)} vs. {len(circuits)} circuits."
            )

        # Step 3: Aggregate survival probabilities
        logging.info("[3/4] Aggregating survival probabilities by depth...")
        agg_data = self._aggregate_results(raw_results, circuits, shots)

        # Step 4: Fit decay curve
        logging.info("[4/4] Performing RB fitting...")
        fit_results = fit_rb_data(
            depths=agg_data.depths,
            means=agg_data.means,
            stds=agg_data.stds,
            num_qubits=self.num_qubits,
        )
        self.results = fit_results

        if fit_results.get("fit_successful"):
            logging.info(f"Fit successful. EPC = {fit_results['epc']:.3e}")
        else:
            logging.warning("Fit failed.")

        # Visualization
        if plot:
            show_plot_at_end = axes is None
            if fit_results.get("fit_successful"):
                current_ax = axes or plt.subplots(figsize=(8, 5))[1]
                title = f"{rb_type} {self.num_qubits}-Qubit RB Decay ({mode} Mode)"
                plot_rb_single(fit_results, title=title, ax=current_ax)
                if show_plot_at_end:
                    plt.tight_layout()
                    plt.show()
            else:
                logging.warning("Skipping plot generation (fit failed).")

        return fit_results


# ---------------------------------------------------------------------
# Interleaved Randomized Benchmarking Experiment
# ---------------------------------------------------------------------
class InterleavedRBExperiment(StandardRBExperiment):
    """Perform Interleaved RB to extract gate-specific error probabilities."""

    def __init__(
        self,
        qubits: Union[int, List[int]],
        interleaved_gate: Gate,
        depths: List[int] = DEFAULT_RB_DEPTHS,
        circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
        native_gates: Optional[List[str]] = None,
        seed: Optional[Union[int, float]] = None,
        clifford_factory: Optional[CliffordFactory] = None,
    ):
        super().__init__(
            qubits=qubits,
            depths=depths,
            circuits_per_depth=circuits_per_depth,
            native_gates=native_gates,
            seed=seed,
            clifford_factory=clifford_factory,
        )
        self.interleaved_gate = interleaved_gate

    def run(
        self,
        engine: Optional[QuantumEngine] = None,
        shots: Optional[int] = None,
        plot: bool = True,
        axes: Optional[plt.Axes] = None,
        experimental_results_ref: Optional[List[Tuple[Dict[str, float], Dict[str, int]]]] = None,
        experimental_results_int: Optional[List[Tuple[Dict[str, float], Dict[str, int]]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Execute the full Interleaved RB workflow (dual-mode)."""
        gate_name = self.interleaved_gate.name.upper()
        mode = (
            "User Data"
            if (experimental_results_ref is not None or experimental_results_int is not None)
            else "Engine"
        )
        logging.info(
            f"--- Running Interleaved {self.num_qubits}-Qubit RB for Gate '{gate_name}' [{mode} Mode] ---"
        )

        # Step 1: Reference RB
        if experimental_results_ref is None:
            std_rb = StandardRBExperiment(
                qubits=self.qubits,
                depths=self.depths,
                circuits_per_depth=self.circuits_per_depth,
                native_gates=self.native_gates,
                seed=self.seed,
                clifford_factory=self.clifford_factory,
            )
            results_std = std_rb.run(engine=engine, shots=shots, plot=False)
        else:
            std_rb = StandardRBExperiment(self.qubits, self.depths, self.circuits_per_depth)
            results_std = std_rb.run(
                shots=shots, plot=False, experimental_results=experimental_results_ref
            )

        if not results_std.get("fit_successful"):
            logging.error("Reference RB fit failed; aborting Interleaved RB.")
            return None

        # Step 2: Interleaved RB
        if experimental_results_int is None:
            results_irb = super().run(engine=engine, shots=shots, plot=False)
        else:
            results_irb = super().run(
                shots=shots, plot=False, experimental_results=experimental_results_int
            )

        if not results_irb.get("fit_successful"):
            logging.error("Interleaved RB fit failed.")
            return None

        # Step 3: Error per Gate Calculation
        epg = calculate_epg(results_std["p"], results_irb["p"], self.num_qubits)

        logging.info(f"Reference EPC = {results_std['epc']:.3e}")
        logging.info(f"Interleaved EPC = {results_irb['epc']:.3e}")
        logging.info(f"Derived Gate EPG ({gate_name}) = {epg:.3e}")

        results_irb["epg"] = epg
        self.results = {
            "epg": epg,
            "standard_results": results_std,
            "interleaved_results": results_irb,
        }

        # Visualization
        if plot:
            show_plot_at_end = axes is None
            current_ax = axes or plt.subplots(figsize=(8, 5))[1]
            plot_rb_comparison(results_std, results_irb, target_gate_name=gate_name, ax=current_ax)
            if show_plot_at_end:
                plt.tight_layout()
                plt.show()

        return self.results