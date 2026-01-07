# =============================================================================
# File    : egm/core/experiments/benchmarking/xeb.py
# Version : v5.2.0 - RB-Schema + SISQ-Compatible Edition
# =============================================================================
"""
Cross-Entropy Benchmarking (XEB) Controller - RB-Unified & SISQ-Compatible
==========================================================================

This module provides a unified XEB controller compatible with the
Randomized Benchmarking (RB) schema while incorporating all features and
interfaces from the SISQ experimental XEB framework.

Key Features
------------
* Unified RB-style result schema and plotting
* Dual-mode operation: simulation or user-supplied experimental data
* Extended run() interface with support for:
  - experimental_results
  - experimental_data_by_depth
  - noisy_data_by_depth
  - ideal_probs_by_depth
* Native-gate decomposition and uniform-distribution rejection
* Per-depth generation statistics and debug logging
* Dual-subplot visualization (XEB / SPB decay)
"""

from __future__ import annotations
import logging
import random
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import matplotlib

# Force a GUI-enabled backend for interactive visualization
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

# -------------------------------------------------------------------------
# tqdm (optional dependency)
# -------------------------------------------------------------------------
try:
    from tqdm import tqdm

    _TQDM_AVAILABLE = True
except ImportError:
    _TQDM_AVAILABLE = False

    def tqdm(iterator, *_, **__):
        """Fallback simple iterator if tqdm is not installed."""
        return iterator


# -------------------------------------------------------------------------
# Internal imports
# -------------------------------------------------------------------------
from egm.core.circuits.circuit import QuantumCircuit, Gate
from egm.core.circuits.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set
from egm.core.engine.executor import QuantumEngine
from egm.core.analysis.xeb import fit_xeb_data, analyze_xeb_and_spb_from_results
from egm.core.analysis.spb import fit_spb_data
from egm.reporting.visualizers.xeb_plotter import plot_xeb_decay
from egm.reporting.visualizers.spb_plotter import plot_spb_decay
from egm.core.backends.ideal_backend import IdealBackend
from egm.core.backends.base_backend import BaseBackend

# -------------------------------------------------------------------------
# Logging configuration
# -------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_DEPTHS = [0, 2, 4, 6, 8, 12, 20, 32, 40]
DEFAULT_CIRCUITS_PER_DEPTH = 10


# =============================================================================
# Utility
# =============================================================================
def _validate_qubit_list(qubits: Any, name="qubits"):
    """Ensure that a valid list of integer qubit indices is provided."""
    if not isinstance(qubits, (list, tuple)) or not all(isinstance(q, int) for q in qubits):
        raise TypeError(f"{name} must be a list of integers.")


# =============================================================================
# Standard XEB Experiment (RB-Unified + SISQ-Enhanced)
# =============================================================================
class StandardXEBExperiment:
    """Cross-Entropy Benchmarking controller compatible with both RB-schema and SISQ frameworks."""

    def __init__(
        self,
        qubits: List[int],
        depths: List[int] = DEFAULT_DEPTHS,
        circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
        gate_set: Union[str, Dict, BaseGateSet] = "sycamore_xeb",
        seed: Optional[int] = None,
        native_gates: Optional[List[str]] = None,
        topology: Optional[List[Tuple[int, int]]] = None,
        x_axis_mode: str = "gate_count",
        reject_uniform_circuits: bool = True,
        entropy_threshold: float = 0.999,
        max_generation_attempts: int = 10,
        mode: str = "auto",
    ):
        _validate_qubit_list(qubits)
        self.qubits = list(qubits)
        self.num_qubits = len(qubits)
        self.depths = list(depths)
        self.circuits_per_depth = circuits_per_depth
        self.gate_set_spec = gate_set
        self.gate_set_obj = get_gate_set(gate_set)
        self.native_gates = native_gates
        self.topology = topology or self._default_topology()
        self.seed = seed
        self.x_axis_mode = x_axis_mode
        self.reject_uniform_circuits = reject_uniform_circuits
        self.entropy_threshold = entropy_threshold
        self.max_generation_attempts = max_generation_attempts
        self.mode = mode
        self._circuits: Optional[List[QuantumCircuit]] = None
        self.results: Dict[str, Any] = {}
        self._rejection_stats: Dict[int, Dict[str, int]] = {}

    def _default_topology(self):
        """Return a default linear topology if none is provided."""
        if len(self.qubits) < 2:
            return []
        return list(zip(self.qubits, self.qubits[1:]))

    def _is_uniform_distribution(self, probs: Dict[str, float]) -> Tuple[bool, float]:
        """Check whether the probability distribution is near-uniform."""
        vals = np.array(list(probs.values()), float)
        vals = vals[vals > 0]
        if len(vals) == 0:
            return True, 1.0
        h = -np.sum(vals * np.log(vals))
        h_max = np.log(2 ** self.num_qubits)
        h_norm = h / h_max
        return h_norm > self.entropy_threshold, h_norm

    def _generate_circuit(
        self,
        depth: int,
        seed: Optional[int],
        interleaved_gate: Optional[Gate] = None,
    ):
        """Generate a randomized XEB circuit for a specific depth."""
        rng = random.Random(seed)
        circ = QuantumCircuit(qubits=self.qubits)

        if depth == 0:
            circ.measure_all()
            circ.metadata.update({"depth": 0, "seed": seed})
            return circ

        pattern_a = self.topology[0::2]
        pattern_b = self.topology[1::2]

        for d in range(depth):
            circ.add_gates(self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random()))
            if self.topology and isinstance(self.gate_set_obj, TwoQubitGateSet):
                pairs = pattern_a if d % 2 == 0 else pattern_b
                circ.add_gates(self.gate_set_obj.get_random_2q_layer(pairs, seed=rng.random()))
            if interleaved_gate:
                circ.add_gate(interleaved_gate)

        circ.add_gates(self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random()))
        circ.measure_all()

        circ.metadata.update(
            {
                "depth": depth,
                "gate_count": sum(1 for g in circ.gates if not g.is_measurement),
                "seed": seed,
            }
        )

        if self.native_gates:
            try:
                circ = circ.decompose(basis_gates=self.native_gates)
            except Exception as e:
                logger.warning(f"[WARN] Auto-decomposition failed: {e}")
        return circ

    def generate_single_circuit(self, depth: int, seed: Optional[int] = None) -> QuantumCircuit:
        """Generate a single circuit."""
        return self._generate_circuit(depth, seed)

    def circuits(self) -> List[QuantumCircuit]:
        """Generate all valid circuits and cache them."""
        if self._circuits is not None:
            return self._circuits

        rng = random.Random(self.seed)
        ideal_backend = IdealBackend()
        all_circuits: List[QuantumCircuit] = []

        for depth in self.depths:
            valids, attempts, rejected = [], 0, 0
            max_attempts = self.max_generation_attempts * self.circuits_per_depth
            while len(valids) < self.circuits_per_depth and attempts < max_attempts:
                attempts += 1
                c = self._generate_circuit(depth, rng.random())
                if self.reject_uniform_circuits and depth > 0:
                    try:
                        state = ideal_backend.get_statevector(c)
                        probs = ideal_backend.statevector_to_probs(state)
                        is_uniform, entropy = self._is_uniform_distribution(probs)
                        if is_uniform:
                            rejected += 1
                            continue
                    except Exception as e:
                        logger.warning(f"[WARN] Uniform-check failed (depth={depth}): {e}")
                valids.append(c)
            all_circuits.extend(valids)
            self._rejection_stats[depth] = {
                "generated": attempts,
                "rejected": rejected,
                "accepted": len(valids),
            }
            logger.info(f"[CIRCUITS] depth={depth} accepted={len(valids)}")
        self._circuits = all_circuits
        return all_circuits

    def _run_simulation_mode(
        self,
        engine: Optional[QuantumEngine],
        circuits: List[QuantumCircuit],
        shots: int,
        show_progress: bool,
        debug: bool = False,
    ):
        """Run circuits via simulation and collect {(ideal, noisy)} pairs."""
        results_by_depth = defaultdict(list)

        if engine is None:
            ideal_backend = IdealBackend()

            class _VoidBackend(BaseBackend):
                def run(self, circ, s):
                    return None, {}

            engine = QuantumEngine(_VoidBackend())
            engine.ideal_backend = ideal_backend

        iterator = tqdm(circuits, disable=not (_TQDM_AVAILABLE and show_progress))
        all_results = engine.execute_with_ideal(iterator, shots=shots)

        for circ, (ideal, noisy) in zip(circuits, all_results):
            depth = circ.metadata["depth"]
            is_uniform, _ = self._is_uniform_distribution(ideal)
            if self.reject_uniform_circuits and is_uniform:
                continue
            results_by_depth[depth].append((ideal, noisy))

        if debug:
            logger.debug(f"[DEBUG] Simulation results collected for depths: {list(results_by_depth.keys())}")
        return results_by_depth

    def _aggregate_results(
        self,
        raw_results: Dict[int, List[Tuple[Dict[str, float], Dict[str, float]]]],
    ) -> Dict[str, Dict[int, float]]:
        """
        Aggregate circuit-level results into per-depth mean proxies
        for debugging or quick validation before formal analysis.
        """
        fidelities_mean: Dict[int, float] = {}
        purities_mean: Dict[int, float] = {}

        for depth, samples in raw_results.items():
            fidelities = [np.mean(list(ideal.values())) for (ideal, _) in samples]
            purities = [np.mean(list(obs.values())) for (_, obs) in samples]
            fidelities_mean[depth] = float(np.mean(fidelities)) if fidelities else 0.0
            purities_mean[depth] = float(np.mean(purities)) if purities else 0.0

        return {"xeb_means": fidelities_mean, "spb_means": purities_mean}

    def run(
        self,
        circuits: Optional[List[QuantumCircuit]] = None,
        engine: Optional[QuantumEngine] = None,
        shots: int = 2048,
        plot: bool = True,
        experimental_results: Optional[List[Dict[str, float]]] = None,
        experimental_data_by_depth: Optional[Dict[int, List[Dict[str, float]]]] = None,
        noisy_data_by_depth: Optional[Dict[int, List[Dict[str, float]]]] = None,
        ideal_probs_by_depth: Optional[Dict[int, List[Dict[str, float]]]] = None,
        show_progress: bool = True,
        debug: bool = False,
        **plot_kwargs,
    ) -> Dict[str, Any]:
        """Main entry for unified (simulation / user data) experiment run."""
        if debug:
            logger.setLevel(logging.DEBUG)
            print("[DEBUG] Enabled detailed XEB/SPB logging.")

        circuits = circuits or self.circuits()
        experimental_data_by_depth = experimental_data_by_depth or noisy_data_by_depth
        mode = (
            "simulation"
            if engine is not None
            else "user_data"
            if (experimental_data_by_depth or experimental_results)
            else "simulation"
        )
        logger.info(f"[INFO] Starting Standard-XEB ({self.num_qubits}Q) | mode={mode}")

        # Acquire data
        if mode == "simulation":
            results_by_depth = self._run_simulation_mode(engine, circuits, shots, show_progress, debug)
        else:
            ideal_backend = IdealBackend()
            results_by_depth = defaultdict(list)
            for idx, circ in enumerate(circuits):
                depth = circ.metadata.get("depth", 0)
                ideal_probs = ideal_backend.statevector_to_probs(
                    ideal_backend.get_statevector(circ)
                )
                datasets = []
                if experimental_data_by_depth and depth in experimental_data_by_depth:
                    datasets = experimental_data_by_depth[depth]
                elif experimental_results and idx < len(experimental_results):
                    datasets = [experimental_results[idx]]
                for noisy_dict in datasets:
                    results_by_depth[depth].append((ideal_probs, noisy_dict))

        # Compute fidelities/purities
        from egm.core.analysis.xeb import analyze_xeb_fidelity
        from egm.core.analysis.spb import analyze_speckle_purity

        fidelities, purities = {}, {}
        for depth, pairs in results_by_depth.items():
            f_list, p_list = [], []
            for ideal_probs, noisy_counts in pairs:
                f_val = analyze_xeb_fidelity(ideal_probs, noisy_counts, self.num_qubits)
                p_val = analyze_speckle_purity(ideal_probs, noisy_counts, self.num_qubits)
                f_list.append(f_val)
                p_list.append(p_val)
            fidelities[depth] = f_list
            purities[depth] = p_list

        # Curve fitting
        try:
            xeb_fit = fit_xeb_data(fidelities=fidelities, num_qubits=self.num_qubits)
            spb_fit = fit_spb_data(purities=purities, num_qubits=self.num_qubits)
        except Exception as e:
            logger.warning(f"[WARN] Analysis fit failed: {e}")
            xeb_fit = {"p": 0, "epc": 0, "r_squared": 0}
            spb_fit = {"p_c": 0, "r_squared": 0}

        self.results = {
            "xeb_analysis": {
                "raw_data": {int(d): float(np.mean(fidelities[d])) for d in fidelities},
                "fit_results": xeb_fit,
            },
            "spb_analysis": {
                "raw_data": {int(d): float(np.mean(purities[d])) for d in purities},
                "fit_results": spb_fit,
            },
            "xeb_fit": xeb_fit,
            "spb_fit": spb_fit,
        }

        logger.info(f"[XEB] p={xeb_fit['p']:.5f}, EPC={xeb_fit['epc']:.3e}, R^2={xeb_fit['r_squared']:.4f}")
        logger.info(f"[SPB] p_c={spb_fit['p_c']:.5f}, R^2={spb_fit['r_squared']:.4f}")

        if plot:
            self._plot_results(title=f"XEB on qubits {self.qubits}", **plot_kwargs)
        return self.results

    def _plot_results(self, title: str, **kwargs):
        """Visualize XEB and SPB decay fits."""
        plt.close("all")
        fig, (ax_xeb, ax_spb) = plt.subplots(2, 1, figsize=(6.4, 5.8), sharex=True)
        fig.suptitle(title, fontsize=12)
        plot_xeb_decay(
            raw_data=self.results["xeb_analysis"]["raw_data"],
            fit_results=self.results["xeb_analysis"]["fit_results"],
            ax=ax_xeb,
            axis_mode=self.x_axis_mode,
            color="orange",
            error_bar_mode="sem",
            show=False,
            **kwargs,
        )
        ax_xeb.set_ylabel("Mean XEB Fidelity")
        plot_spb_decay(
            raw_data=self.results["spb_analysis"]["raw_data"],
            fit_results=self.results["spb_analysis"]["fit_results"],
            ax=ax_spb,
            axis_mode=self.x_axis_mode,
            color="#ff7f0e",
            error_bar_mode="sem",
            show=False,
            **kwargs,
        )
        ax_spb.set_ylabel("Mean State Purity")
        ax_spb.set_xlabel("Depth" if self.x_axis_mode != "gate_count" else "Gate Count")
        for ax in (ax_xeb, ax_spb):
            ax.grid(True, linestyle="--", linewidth=0.6)
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show(block=True)





# =============================================================================
# Enhanced Interleaved XEB Experiment (EGM v5.3)
# =============================================================================
class InterleavedXEBExperiment(StandardXEBExperiment):
    """
    Interleaved Cross-Entropy Benchmarking (XEB) Controller — Enhanced version.

    Adds entropy checking, rejection of near-uniform circuits,
    and adaptive retry mechanism.
    """

    def __init__(
        self,
        qubits: List[int],
        interleaved_gate,
        reject_uniform_circuits: bool = True,
        entropy_threshold: float = 0.999,
        max_generation_attempts: int = 10,
        **kwargs,
    ):
        """
        Parameters
        ----------
        qubits : List[int]
            List of qubit indices.
        interleaved_gate : Gate
            The target gate to interleave between random layers.
        reject_uniform_circuits : bool, optional
            If True, discard random circuits with nearly uniform
            output distributions.
        entropy_threshold : float
            Normalized entropy threshold (values close to 1 -> uniform).
        max_generation_attempts : int
            Maximum multiple of the nominal circuit count to retry.
        kwargs : dict
            Passed through to StandardXEBExperiment.
        """
        super().__init__(qubits, **kwargs)
        self.interleaved_gate = interleaved_gate
        self.reject_uniform_circuits = reject_uniform_circuits
        self.entropy_threshold = entropy_threshold
        self.max_generation_attempts = max_generation_attempts
        self._circuits_ref: Optional[List[Any]] = None
        self._circuits_int: Optional[List[Any]] = None

    # ----------------------------------------------------------------------
    def _is_uniform_distribution(self, probs: Dict[str, float]) -> Tuple[bool, float]:
        """Return (is_uniform, normalized_entropy)."""
        v = np.array(list(probs.values()), float)
        v = v[v > 0]
        if len(v) == 0:
            return True, 1.0
        h = -np.sum(v * np.log(v))
        h_max = np.log(2 ** self.num_qubits)
        h_norm = h / h_max
        return h_norm > self.entropy_threshold, h_norm

    # ----------------------------------------------------------------------
    def _generate_reference_circuit(self, depth: int, seed: Optional[int]):
        return self._generate_circuit(depth, seed, interleaved_gate=None)

    def _generate_interleaved_circuit(self, depth: int, seed: Optional[int]):
        return self._generate_circuit(depth, seed, interleaved_gate=self.interleaved_gate)

    # ----------------------------------------------------------------------
    def circuits(self, mode: str = "interleaved") -> List[Any]:
        """Generate reference or interleaved circuits with rejection filtering."""
        rng = random.Random(self.seed)
        ideal_backend = IdealBackend()
        all_circuits: List[Any] = []

        for depth in self.depths:
            valids: List[Any] = []
            attempts = 0
            rejected = 0
            max_attempts = self.max_generation_attempts * self.circuits_per_depth

            while len(valids) < self.circuits_per_depth and attempts < max_attempts:
                attempts += 1
                s = rng.random()
                circ = (
                    self._generate_reference_circuit(depth, s)
                    if mode == "reference"
                    else self._generate_interleaved_circuit(depth, s)
                )

                if self.reject_uniform_circuits and depth > 0:
                    try:
                        state = ideal_backend.get_statevector(circ)
                        probs = ideal_backend.statevector_to_probs(state)
                        is_uniform, h_norm = self._is_uniform_distribution(probs)
                        if is_uniform:
                            rejected += 1
                            continue
                    except Exception as e:
                        logger.warning(f"[WARN] Uniform check failed at depth={depth}: {e}")
                valids.append(circ)

            if len(valids) < self.circuits_per_depth:
                logger.warning(
                    f"[WARN] depth={depth}: only {len(valids)} valid circuits "
                    f"after {attempts} attempts ({rejected} rejected)."
                )
            all_circuits.extend(valids)

        if mode == "reference":
            self._circuits_ref = all_circuits
        else:
            self._circuits_int = all_circuits
        return all_circuits

    # ----------------------------------------------------------------------
    def _aggregate_results(
        self,
        ref_results: Dict[int, List[Tuple[Dict[str, float], Dict[str, float]]]],
        int_results: Dict[int, List[Tuple[Dict[str, float], Dict[str, float]]]],
    ) -> Dict[str, Dict[int, float]]:
        """
        Aggregate both reference and interleaved circuit-level results
        into mean fidelity and purity per depth.

        Parameters
        ----------
        ref_results : Dict[int, List[Tuple[Dict, Dict]]]
            Reference dataset by depth.
        int_results : Dict[int, List[Tuple[Dict, Dict]]]
            Interleaved dataset by depth.

        Returns
        -------
        Dict[str, Dict[int, float]]
            {
                "ref_xeb": {depth: mean_fidelity},
                "ref_spb": {depth: mean_purity},
                "int_xeb": {depth: mean_fidelity},
                "int_spb": {depth: mean_purity}
            }
        """
        ref_xeb, ref_spb, int_xeb, int_spb = {}, {}, {}, {}

        for depth, samples in ref_results.items():
            f_vals = [np.mean(list(ideal.values())) for (ideal, _) in samples]
            p_vals = [np.mean(list(obs.values())) for (_, obs) in samples]
            ref_xeb[depth] = float(np.mean(f_vals)) if f_vals else 0.0
            ref_spb[depth] = float(np.mean(p_vals)) if p_vals else 0.0

        for depth, samples in int_results.items():
            f_vals = [np.mean(list(ideal.values())) for (ideal, _) in samples]
            p_vals = [np.mean(list(obs.values())) for (_, obs) in samples]
            int_xeb[depth] = float(np.mean(f_vals)) if f_vals else 0.0
            int_spb[depth] = float(np.mean(p_vals)) if p_vals else 0.0

        return {
            "ref_xeb": ref_xeb,
            "ref_spb": ref_spb,
            "int_xeb": int_xeb,
            "int_spb": int_spb,
        }

    # ----------------------------------------------------------------------
    def run(
        self,
        engine=None,
        shots: int = 2048,
        experimental_data_by_depth_ref: Optional[Dict[int, List[Dict[str, float]]]] = None,
        experimental_data_by_depth_int: Optional[Dict[int, List[Dict[str, float]]]] = None,
        show_progress: bool = True,
        plot: bool = True,
        debug: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run both reference and interleaved circuits and compute gate fidelity."""
        logger.info(f"[INFO] Running Interleaved-XEB for gate '{self.interleaved_gate.name}'")

        circuits_ref = self._circuits_ref or self.circuits("reference")
        circuits_int = self._circuits_int or self.circuits("interleaved")

        mode = (
            "simulation"
            if engine is not None
            else "user_data"
            if (experimental_data_by_depth_ref or experimental_data_by_depth_int)
            else "simulation"
        )

        if mode == "user_data":
            logger.info("[MODE] User-data mode detected (manual fidelity analysis)")
            ideal_backend = IdealBackend()
            ref_results, int_results = defaultdict(list), defaultdict(list)
            for circ in circuits_ref:
                depth = circ.metadata.get("depth", 0)
                ideal_probs = ideal_backend.statevector_to_probs(
                    ideal_backend.get_statevector(circ)
                )
                for noisy in (
                    experimental_data_by_depth_ref.get(depth, [])
                    if experimental_data_by_depth_ref
                    else []
                ):
                    ref_results[depth].append((ideal_probs, noisy))
            for circ in circuits_int:
                depth = circ.metadata.get("depth", 0)
                ideal_probs = ideal_backend.statevector_to_probs(
                    ideal_backend.get_statevector(circ)
                )
                for noisy in (
                    experimental_data_by_depth_int.get(depth, [])
                    if experimental_data_by_depth_int
                    else []
                ):
                    int_results[depth].append((ideal_probs, noisy))
        else:
            logger.info("[MODE] Simulation mode activated")
            ref_results = self._run_simulation_mode(engine, circuits_ref, shots, show_progress)
            int_results = self._run_simulation_mode(engine, circuits_int, shots, show_progress)

        ref_analysis = analyze_xeb_and_spb_from_results(
            ref_results, num_qubits=self.num_qubits, circuits=circuits_ref, axis_mode=self.x_axis_mode
        )
        int_analysis = analyze_xeb_and_spb_from_results(
            int_results, num_qubits=self.num_qubits, circuits=circuits_int, axis_mode=self.x_axis_mode
        )

        p_ref = ref_analysis["xeb_analysis"]["fit_results"].get("p", 0)
        p_int = int_analysis["xeb_analysis"]["fit_results"].get("p", 0)

        d = 2 ** len(self.interleaved_gate.qubits)
        ratio_raw = p_int / p_ref if p_ref != 0 else 0.0
        ratio = np.clip(ratio_raw, 0, 1)
        gate_error = (d - 1) / d * (1 - ratio)
        gate_fidelity = 1 - gate_error

        self.results = {
            "reference": ref_analysis,
            "interleaved": int_analysis,
            "gate_fidelity": gate_fidelity,
            "gate_error": gate_error,
            "ratio_raw": ratio_raw,
            "ratio": ratio,
        }

        if debug:
            logger.debug(
                f"[DEBUG] p_ref={p_ref:.6f}, p_int={p_int:.6f}, ratio={ratio:.6f} "
                f"-> fidelity={gate_fidelity:.6f}"
            )

        if plot:
            self._plot_interleaved()
        return self.results

    # ----------------------------------------------------------------------
    def _plot_interleaved(self):
        """
        RB-style Interleaved-XEB/SPB plot.

        Both reference (blue) and interleaved (orange) use dashed lines,
        white-filled markers, and visible error bars.
        """
        import matplotlib.pyplot as plt
        import numpy as np

        plt.ioff()
        ref = self.results.get("reference", {})
        inter = self.results.get("interleaved", {})

        COLOR = {
            "ref": "#1f77b4",  # blue
            "int": "#ff7f0e",  # orange
        }

        fig, (ax_xeb, ax_spb) = plt.subplots(2, 1, figsize=(8.0, 6.0), sharex=True)
        fig.suptitle(
            f"Interleaved XEB - {self.interleaved_gate.name}",
            fontsize=14,
            fontweight="semibold",
        )

        def _draw_decay(ax, analysis_key, data, label, color):
            """Draw one dataset (mean + error bars + dashed fit line)."""
            if not data or analysis_key not in data:
                return
            ana = data[analysis_key]
            raw = ana.get("raw_data", {})
            fit = ana.get("fit_results", {})
            if not raw:
                return

            x_vals = np.array(sorted(raw.keys()), dtype=float)
            y_vals = np.array(
                [
                    np.mean(raw[k]) if isinstance(raw[k], (list, np.ndarray)) else float(raw[k])
                    for k in sorted(raw.keys())
                ],
                dtype=float,
            )

            # Error bars
            std_errors = fit.get("std_errors", None)
            if isinstance(std_errors, dict):
                yerr = np.array([std_errors.get(int(x), 0.005) for x in x_vals])
            elif isinstance(std_errors, (list, tuple, np.ndarray)):
                yerr = np.array(std_errors, dtype=float)
                if len(yerr) < len(x_vals):
                    yerr = np.pad(yerr, (0, len(x_vals) - len(yerr)), constant_values=0.005)
            else:
                yerr = np.full_like(y_vals, 0.005)
            yerr_visible = np.maximum(yerr, 0.002) * 3.0

            ax.errorbar(
                x_vals,
                y_vals,
                yerr=yerr_visible,
                fmt="o",
                color=color,
                mfc="white",
                mec=color,
                ecolor=color,
                elinewidth=0.9,
                capsize=3,
                markersize=4.5,
                alpha=0.9,
                label=label,
            )

            # Fit curve (dashed line)
            if all(k in fit for k in ("A", "B")):
                p = fit.get("p") or fit.get("p_c") or fit.get("p_fit", 1.0)
                A = fit["A"]
                B = fit["B"]
                fx = np.linspace(np.min(x_vals), np.max(x_vals), 300)
                fy = A * (p ** fx) + B
                ax.plot(fx, fy, "--", lw=1.6, color=color, alpha=0.9)

        # --- XEB Plot ----------------------------------------------------
        _draw_decay(
            ax_xeb,
            "xeb_analysis" if "xeb_analysis" in ref else "xeb",
            ref,
            "Reference XEB",
            COLOR["ref"],
        )
        _draw_decay(
            ax_xeb,
            "xeb_analysis" if "xeb_analysis" in inter else "xeb",
            inter,
            "Interleaved XEB",
            COLOR["int"],
        )
        ax_xeb.set_ylabel("Mean XEB Fidelity")
        ax_xeb.legend(frameon=False, loc="lower right")
        ax_xeb.set_title("Cross-Entropy Benchmarking (XEB) Decay", fontweight="bold", pad=4)
        ax_xeb.grid(True, linestyle="--", linewidth=0.6)

        # --- SPB Plot ----------------------------------------------------
        _draw_decay(
            ax_spb,
            "spb_analysis" if "spb_analysis" in ref else "spb",
            ref,
            "Reference SPB",
            COLOR["ref"],
        )
        _draw_decay(
            ax_spb,
            "spb_analysis" if "spb_analysis" in inter else "spb",
            inter,
            "Interleaved SPB",
            COLOR["int"],
        )
        ax_spb.set_ylabel("Mean State Purity")
        ax_spb.legend(frameon=False, loc="lower right")
        ax_spb.set_title("State-Purity Benchmarking (SPB) Decay", fontweight="bold", pad=4)
        ax_spb.grid(True, linestyle="--", linewidth=0.6)

        xlabel = (
            "Total 1-Q Gate Count" if self.x_axis_mode == "gate_count" else "Circuit Depth"
        )
        ax_spb.set_xlabel(xlabel)

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show(block=True)
        plt.ion()