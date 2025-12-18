# File: egm/core/experiments/benchmarking/xeb.py
# [v4.3 — Final Unified Version | RB‑Style Architecture]
# ---------------------------------------------------------------------
# Cross‑Entropy Benchmarking (XEB) Experiment Definitions
# ---------------------------------------------------------------------
# Implements standardized Standard XEB and Interleaved XEB protocols:
#   • Dual operation modes: Engine (simulation) / User‑Data (analysis)
#   • Automatic unpacking of (ideal, noisy) tuples for compatibility
#   • Circuit generation aligned with RB‑style experiment architecture
#   • Integrated XEB + SPB analysis with publication‑ready plotting
# ---------------------------------------------------------------------

from __future__ import annotations
import random
import logging
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Optional, Union, cast
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Internal Imports
# ---------------------------------------------------------------------
from egm.core.circuits.circuit import QuantumCircuit, Gate
from egm.core.circuits.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set
from egm.core.engine.executor import QuantumEngine
from egm.core.analysis.xeb import analyze_xeb_and_spb_from_results
from egm.reporting.visualizers.xeb_plotter import plot_xeb_decay, plot_spb_decay

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------
DEFAULT_DEPTHS = [0, 5, 10, 15, 25, 40, 60]
DEFAULT_NUM_CIRCUITS = 30
DEFAULT_NATIVE_GATES = ["cz", "sx", "rz", "h", "s"]


# ---------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------
def _validate_qubits(qubits: Any) -> None:
    """Sanity‑check that the qubits specification is a list of integers."""
    if not isinstance(qubits, (list, tuple)) or not all(isinstance(q, int) for q in qubits):
        raise TypeError("Parameter 'qubits' must be a list of integers.")


# =====================================================================
# CLASS: Standard XEB Experiment
# =====================================================================
class StandardXEBExperiment:
    """
    Implements the Standard Cross‑Entropy Benchmarking (XEB) protocol.

    Supports both Engine‑executed and User‑supplied data modes. The experiment
    generates a randomized two‑qubit circuit ensemble, executes or analyzes it,
    and fits both XEB fidelity and SPB purity decay.
    """

    # -----------------------------------------------------------------
    # Initialization
    # -----------------------------------------------------------------
    def __init__(
        self,
        qubits: List[int],
        depths: List[int] = DEFAULT_DEPTHS,
        circuits_per_depth: int = DEFAULT_NUM_CIRCUITS,
        gate_set: Union[str, Dict, BaseGateSet] = "universal_xeb",
        native_gates: Optional[List[str]] = DEFAULT_NATIVE_GATES,
        seed: Optional[Union[int, float]] = None,
        topology: Optional[List[Tuple[int, int]]] = None,
    ):
        _validate_qubits(qubits)
        self.qubits = qubits
        self.num_qubits = len(qubits)
        self.depths = sorted(set(depths))
        self.circuits_per_depth = circuits_per_depth
        self.gate_set_spec = gate_set
        self.gate_set_obj = get_gate_set(gate_set)
        self.native_gates = native_gates
        self.seed = seed
        self.topology = topology or self._default_topology()
        self._circuits: Optional[List[QuantumCircuit]] = None
        self.results: Optional[Dict[str, Any]] = None

        logger.info(
            f"Initialized Standard XEB on {self.num_qubits} qubits with depths {self.depths}"
        )

    # -----------------------------------------------------------------
    def _default_topology(self) -> List[Tuple[int, int]]:
        """Provide a linear nearest‑neighbor topology as default connectivity."""
        return list(zip(self.qubits, self.qubits[1:])) if len(self.qubits) > 1 else []

    # -----------------------------------------------------------------
    # Circuit Generation
    # -----------------------------------------------------------------
    def _generate_circuit(
        self,
        depth: int,
        seed: Optional[Union[int, float]],
        interleaved_gate: Optional[Gate] = None,
    ) -> QuantumCircuit:
        """Internal: construct a single XEB circuit at specified depth."""
        rng = random.Random(seed)
        circuit = QuantumCircuit(qubits=self.qubits)

        # Identity (depth = 0)
        if depth == 0:
            circuit.measure_all()
            circuit.metadata.update({"depth": 0, "seed": seed})
            if interleaved_gate:
                circuit.metadata["interleaved_gate_name"] = interleaved_gate.name
            return circuit

        # Layered structure: alternating 1Q + 2Q layers
        pattern_a, pattern_b = self.topology[0::2], self.topology[1::2]
        for d in range(depth):
            single_q_layer = self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random())
            circuit.add_gates(single_q_layer)

            if self.topology and isinstance(self.gate_set_obj, TwoQubitGateSet):
                pattern = pattern_a if d % 2 == 0 else pattern_b
                two_q_layer = self.gate_set_obj.get_random_2q_layer(pattern, seed=rng.random())
                circuit.add_gates(two_q_layer)

            if interleaved_gate:
                circuit.add_gate(interleaved_gate)

        # Final single‑qubit layer + measurement
        final_layer = self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random())
        circuit.add_gates(final_layer)
        circuit.measure_all()

        circuit.metadata.update({"depth": depth, "seed": seed})
        if interleaved_gate:
            circuit.metadata["interleaved_gate_name"] = interleaved_gate.name
        return circuit

    # -----------------------------------------------------------------
    def generate_single_circuit(
        self,
        depth: int,
        seed: Optional[Union[int, float]] = None,
        interleaved_gate: Optional[Gate] = None,
    ) -> QuantumCircuit:
        """Generate and optionally decompose a single compiled XEB circuit."""
        circuit = self._generate_circuit(depth, seed, interleaved_gate)
        if self.native_gates:
            circuit = circuit.decompose(basis_gates=self.native_gates)
        circuit.metadata["noise_exponent"] = sum(1 for g in circuit.gates if not g.is_measurement)
        return circuit

    # -----------------------------------------------------------------
    def circuits(self) -> List[QuantumCircuit]:
        """Return (and cache) the full ensemble of benchmark circuits."""
        if self._circuits is not None:
            return self._circuits
        rng = random.Random(self.seed)
        circuits: List[QuantumCircuit] = []
        for d in self.depths:
            for _ in range(self.circuits_per_depth):
                c_seed = rng.random()
                circuits.append(self.generate_single_circuit(d, c_seed))
        self._circuits = circuits
        return circuits

    # -----------------------------------------------------------------
    # Core Execution / Analysis Entry Point
    # -----------------------------------------------------------------
    def run(
        self,
        engine: QuantumEngine,
        shots: int = 2048,
        plot: bool = True,
        axes: Optional[Tuple[plt.Axes, plt.Axes]] = None,
        show_progress: bool = True,
        experimental_results: Optional[List[Any]] = None,
        **plot_kwargs,
    ) -> Dict[str, Any]:
        """
        Execute or analyze a complete XEB experiment.

        Supports:
            • **Engine Mode** — run circuits on a backend or simulator.  
            • **User Data Mode** — analyze externally supplied measurement results.

        Args:
            engine:   QuantumEngine backend or simulator.
            shots:    Number of measurement shots per circuit.
            plot:     Whether to automatically plot analysis results.
            axes:     Optional matplotlib axes for embedded plotting.
            show_progress:  Display progress bar if 'tqdm' available.
            experimental_results: Pre‑recorded result dictionaries or tuples.
        """
        mode = "User Data" if experimental_results else "Engine"
        logger.info(f"--- Running {self.num_qubits}‑Qubit Standard XEB [{mode} Mode] ---")

        circuits = self.circuits()
        results_by_depth = defaultdict(list)

        # --------------------------------------------------------------
        # USER‑DATA MODE
        # --------------------------------------------------------------
        if experimental_results is not None:
            if len(experimental_results) != len(circuits):
                raise ValueError(
                    f"Experimental results ({len(experimental_results)}) "
                    f"do not match generated circuit count ({len(circuits)})."
                )

            normalized = 0
            for circ, exp_data in zip(circuits, experimental_results):
                depth = circ.metadata.get("depth")

                # 💡 Auto‑detect tuple form → (ideal, noisy)
                if isinstance(exp_data, tuple) and len(exp_data) == 2:
                    _, exp_data = exp_data
                    logger.info(
                        "[INFO] Detected (ideal, noisy) tuple; using 'noisy' distribution."
                    )

                if not isinstance(exp_data, dict):
                    raise TypeError(
                        "Each experimental result must be a dictionary of bitstring → counts or probabilities."
                    )

                total = sum(exp_data.values())
                if total == 0:
                    raise ValueError("Experimental distribution is empty.")

                # Normalize if needed
                if abs(total - 1.0) > 1e-6:
                    exp_data = {k: v / total for k, v in exp_data.items()}
                    normalized += 1

                # Ideal distribution derived from simulation
                ideal_state = engine.get_ideal_statevector(circ)
                ideal_probs = engine._statevector_to_probs(ideal_state, circ.num_qubits)
                results_by_depth[depth].append((ideal_probs, exp_data))

            if normalized:
                logger.info(f"Normalized {normalized} user‑supplied distributions.")

        # --------------------------------------------------------------
        # ENGINE MODE
        # --------------------------------------------------------------
        else:
            try:
                from tqdm import tqdm
                iterator = tqdm(circuits, disable=not show_progress, desc="Executing XEB Circuits")
            except ImportError:
                iterator = circuits

            all_results = engine.execute_with_ideal(iterator, shots)
            for circ, (ideal_probs, noisy_counts) in zip(circuits, all_results):
                depth = circ.metadata["depth"]
                results_by_depth[depth].append((ideal_probs, noisy_counts))

        # --------------------------------------------------------------
        # Unified XEB + SPB Analysis + Visualization
        # --------------------------------------------------------------
        self.results = analyze_xeb_and_spb_from_results(results_by_depth, self.num_qubits)
        if plot:
            title = f"XEB Analysis on Qubits {self.qubits}"
            self._plot_results(axes, title, **plot_kwargs)
        return self.results

    # -----------------------------------------------------------------
    def _plot_results(self, axes, title: str, **kwargs) -> None:
        """Render XEB and SPB decay curves for the current experiment."""
        logger.info("Visualizing XEB + SPB decay results...")
        show = axes is None
        if axes is None:
            fig, axes = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
        ax1, ax2 = cast(Tuple[plt.Axes, plt.Axes], axes)
        fig = ax1.get_figure()
        if show:
            fig.suptitle(title, fontsize=15)

        plot_xeb_decay(
            self.results["xeb_analysis"]["raw_data"],
            self.results["xeb_analysis"]["fit_results"],
            ax=ax1,
            **kwargs,
        )
        plot_spb_decay(
            self.results["spb_analysis"]["raw_data"],
            self.results["spb_analysis"]["fit_results"],
            ax=ax2,
            **kwargs,
        )

        ax1.set_title("XEB Fidelity vs Circuit Depth")
        ax2.set_title("Speckle Purity vs Circuit Depth")
        ax2.set_xlabel("Circuit Depth")
        for ax in (ax1, ax2):
            ax.grid(True, linestyle=":")
            ax.legend()
        if show:
            fig.tight_layout(rect=[0, 0, 1, 0.95])
            plt.show()


# =====================================================================
# CLASS: Interleaved XEB Experiment
# =====================================================================
class InterleavedXEBExperiment(StandardXEBExperiment):
    """
    Implements Interleaved XEB for gate‑specific error characterization.

    Conducts two phases:
        (1) Standard reference XEB on the same qubits.
        (2) Interleaved run inserting a target gate at each cycle.
    """

    # -----------------------------------------------------------------
    def __init__(
        self,
        qubits: List[int],
        interleaved_gate: Gate,
        depths: List[int] = DEFAULT_DEPTHS,
        circuits_per_depth: int = DEFAULT_NUM_CIRCUITS,
        gate_set: Union[str, Dict, BaseGateSet] = "universal_xeb",
        native_gates: Optional[List[str]] = DEFAULT_NATIVE_GATES,
        seed: Optional[Union[int, float]] = None,
        topology: Optional[List[Tuple[int, int]]] = None,
    ):
        super().__init__(qubits, depths, circuits_per_depth, gate_set, native_gates, seed, topology)
        self.interleaved_gate = interleaved_gate

    # -----------------------------------------------------------------
    def circuits(self) -> List[QuantumCircuit]:
        """Generate the full interleaved‑XEB circuit ensemble."""
        if self._circuits is not None:
            return self._circuits
        rng = random.Random(self.seed)
        circuits: List[QuantumCircuit] = []
        for d in self.depths:
            for _ in range(self.circuits_per_depth):
                c_seed = rng.random()
                circuits.append(
                    self.generate_single_circuit(d, c_seed, interleaved_gate=self.interleaved_gate)
                )
        self._circuits = circuits
        return circuits

    # -----------------------------------------------------------------
    def run(
        self,
        engine: QuantumEngine,
        shots: int = 2048,
        plot: bool = True,
        axes: Optional[Tuple[plt.Axes, plt.Axes]] = None,
        show_progress: bool = True,
        experimental_results_ref: Optional[List[Any]] = None,
        experimental_results_int: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """Run both Standard and Interleaved XEB phases, then derive gate error."""
        gate_name = self.interleaved_gate.name
        logger.info(f"--- Running Interleaved XEB for Gate '{gate_name}' ---")

        # Reference Phase
        logger.info("[Phase 1/2] Reference (Standard) XEB…")
        ref_exp = StandardXEBExperiment(
            self.qubits,
            self.depths,
            self.circuits_per_depth,
            self.gate_set_spec,
            self.native_gates,
            self.seed,
            self.topology,
        )
        ref_res = ref_exp.run(
            engine=engine,
            shots=shots,
            plot=False,
            show_progress=show_progress,
            experimental_results=experimental_results_ref,
        )

        # Interleaved Phase
        logger.info("[Phase 2/2] Interleaved Experiment…")
        int_res = super().run(
            engine=engine,
            shots=shots,
            plot=False,
            show_progress=show_progress,
            experimental_results=experimental_results_int,
        )

        # Compute gate‑specific error and fidelity
        p_ref = ref_res["xeb_analysis"]["fit_results"].get("p", 0)
        p_int = int_res["xeb_analysis"]["fit_results"].get("p", 0)
        d = 2 ** len(self.interleaved_gate.qubits)
        gate_error = float("inf") if p_ref == 0 else (d - 1) / d * (1 - p_int / p_ref)
        gate_fid = 1 - gate_error

        self.results = {
            "reference": ref_res,
            "interleaved": int_res,
            "gate_error": gate_error,
            "gate_fidelity": gate_fid,
        }

        if plot:
            self._plot_interleaved_results(axes)
        return self.results

    # -----------------------------------------------------------------
    def _plot_interleaved_results(self, axes) -> None:
        """Overlay and compare Reference vs Interleaved decay curves."""
        logger.info("Plotting Interleaved XEB comparison curves…")
        show = axes is None
        if axes is None:
            fig, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
        ax1, ax2 = cast(Tuple[plt.Axes, plt.Axes], axes)
        fig = ax1.get_figure()
        fig.suptitle(f"Interleaved XEB for Gate '{self.interleaved_gate.name}'", fontsize=15)

        ref = self.results["reference"]
        inter = self.results["interleaved"]

        # XEB Fidelity Curves
        plot_xeb_decay(ref["xeb_analysis"]["raw_data"], ref["xeb_analysis"]["fit_results"],
                       ax=ax1, label="Reference", color="C0")
        plot_xeb_decay(inter["xeb_analysis"]["raw_data"], inter["xeb_analysis"]["fit_results"],
                       ax=ax1, label="Interleaved", color="C2")

        # SPB Purity Curves
        plot_spb_decay(ref["spb_analysis"]["raw_data"], ref["spb_analysis"]["fit_results"],
                       ax=ax2, label="Reference", color="C0")
        plot_spb_decay(inter["spb_analysis"]["raw_data"], inter["spb_analysis"]["fit_results"],
                       ax=ax2, label="Interleaved", color="C2")

        ax1.set_title("XEB Fidelity Comparison")
        ax2.set_title("SPB Purity Comparison")
        ax2.set_xlabel("Circuit Depth")
        for ax in (ax1, ax2):
            ax.grid(True, linestyle=":")
            ax.legend()
        if show:
            fig.tight_layout(rect=[0, 0, 1, 0.95])
            plt.show()