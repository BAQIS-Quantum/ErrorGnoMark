# =============================================================================
# File    : egm/core/experiments/benchmarking/spb.py
# Version : v5.3.0 - SISQ-Compatible Edition
# =============================================================================
"""
egm.core.experiments.benchmarking.spb
=====================================

Speckle-Purity Benchmarking (SPB) Experiment Controller.

- Functionality cloned from sisq-egm-spb v4.3.2
- Structure follows egm-src v4.5 (RB-style) organization
- Provides both Standard and Interleaved SPB experiment workflows
"""

from __future__ import annotations
import random
import logging
import numpy as np
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Optional, Union

from egm.core.circuits.circuit import QuantumCircuit, Gate
from egm.core.circuits.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set
from egm.core.engine.executor import QuantumEngine
from egm.core.analysis.spb import analyze_speckle_purity, fit_spb_decay
from egm.reporting.visualizers.spb_plotter import plot_spb_decay
from egm.core.backends.ideal_backend import IdealBackend
from egm.core.backends.base_backend import BaseBackend

# ---------------------------------------------------------------------------
# Optional progress bar
# ---------------------------------------------------------------------------
try:
    from tqdm import tqdm

    _TQDM_AVAILABLE = True
except ImportError:
    _TQDM_AVAILABLE = False

    def tqdm(x, *_, **__):
        return x


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_DEPTHS = [0, 4, 8, 12, 20, 32]
DEFAULT_CIRCUITS_PER_DEPTH = 15
DEFAULT_NATIVE_GATES = ["cz", "sx", "rz"]


def _validate_qubit_list(qubits: Any):
    """Ensure that 'qubits' is a list of int."""
    if not isinstance(qubits, (list, tuple)) or not all(isinstance(q, int) for q in qubits):
        raise TypeError("'qubits' must be a list of integers.")


# =============================================================================
# CLASS: Standard SPB Experiment
# =============================================================================
class StandardSPBExperiment:
    """Implements the Standard Speckle-Purity Benchmarking workflow."""

    def __init__(
        self,
        qubits: List[int],
        depths: List[int] = DEFAULT_DEPTHS,
        circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
        gate_set: Union[str, Dict, BaseGateSet] = "universal_xeb",
        native_gates: Optional[List[str]] = DEFAULT_NATIVE_GATES,
        seed: Optional[Union[int, float]] = None,
        topology: Optional[List[Tuple[int, int]]] = None,
        reject_uniform_circuits: bool = True,
        entropy_threshold: float = 0.999,
        max_generation_attempts: int = 10,
        x_axis_mode: str = "depth",
    ):
        _validate_qubit_list(qubits)
        self.qubits = qubits
        self.num_qubits = len(qubits)
        self.depths = sorted(set(depths))
        self.circuits_per_depth = circuits_per_depth
        self.gate_set_spec = gate_set
        self.gate_set_obj = get_gate_set(gate_set)
        self.native_gates = native_gates
        self.topology = topology or self._default_topology()
        self.seed = seed
        self.reject_uniform_circuits = reject_uniform_circuits
        self.entropy_threshold = entropy_threshold
        self.max_generation_attempts = max_generation_attempts
        self.x_axis_mode = x_axis_mode
        self._circuits: Optional[List[QuantumCircuit]] = None
        self.results: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    def _default_topology(self) -> List[Tuple[int, int]]:
        """Default linear 1D chain topology."""
        return list(zip(self.qubits, self.qubits[1:])) if len(self.qubits) > 1 else []

    def _is_uniform_distribution(self, probs: Dict[str, float]) -> Tuple[bool, float]:
        """Return whether distribution is close to uniform and its normalized entropy."""
        values = np.array(list(probs.values()), dtype=float)
        values = values[values > 0]
        if len(values) == 0:
            return True, 1.0
        h = -np.sum(values * np.log(values))
        h_max = np.log(2 ** self.num_qubits)
        return (h / h_max) > self.entropy_threshold, h / h_max

    # ------------------------------------------------------------------
    def _generate_circuit(self, depth: int, seed: Optional[Union[int, float]]) -> QuantumCircuit:
        """Generate a speckle-purity circuit for a given depth."""
        rng = random.Random(seed)
        circ = QuantumCircuit(qubits=self.qubits)

        if depth == 0:
            circ.measure_all()
            circ.metadata.update({"depth": 0, "seed": seed})
            return circ

        pattern_a, pattern_b = self.topology[0::2], self.topology[1::2]
        for d in range(depth):
            circ.add_gates(self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random()))
            if self.topology and isinstance(self.gate_set_obj, TwoQubitGateSet):
                pattern = pattern_a if d % 2 == 0 else pattern_b
                circ.add_gates(self.gate_set_obj.get_random_2q_layer(pattern, seed=rng.random()))

        circ.add_gates(self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random()))
        circ.measure_all()
        circ.metadata.update({"depth": depth, "seed": seed})
        return circ

    def generate_single_circuit(self, depth: int, seed: Optional[float] = None) -> QuantumCircuit:
        """Convenience function for single-circuit generation."""
        circ = self._generate_circuit(depth, seed)
        if self.native_gates:
            try:
                circ = circ.decompose(basis_gates=self.native_gates)
            except Exception as e:
                logger.warning(f"Native-gate decomposition failed: {e}")
        circ.metadata["gate_count"] = sum(1 for g in circ.gates if not g.is_measurement)
        return circ

    def circuits(self) -> List[QuantumCircuit]:
        """Generate and cache all valid circuits."""
        if self._circuits is not None:
            return self._circuits
        rng = random.Random(self.seed)
        ideal_backend = IdealBackend()
        circuits = []
        for depth in self.depths:
            valids, attempts = [], 0
            while len(valids) < self.circuits_per_depth and attempts < self.max_generation_attempts * self.circuits_per_depth:
                attempts += 1
                c = self.generate_single_circuit(depth, rng.random())
                if self.reject_uniform_circuits and depth > 0:
                    try:
                        state = ideal_backend.get_statevector(c)
                        probs = ideal_backend.statevector_to_probs(state)
                        is_u, _ = self._is_uniform_distribution(probs)
                        if is_u:
                            continue
                    except Exception as exc:
                        logger.warning(f"Uniform check failed: {exc}")
                valids.append(c)
            circuits.extend(valids)
        self._circuits = circuits
        return circuits

    # ------------------------------------------------------------------
    def _run_simulation_mode(
        self,
        engine: Optional[QuantumEngine],
        circuits: List[QuantumCircuit],
        shots: int,
        show_progress: bool,
    ) -> Dict[int, List[Tuple[Dict[str, float], Dict[str, float]]]]:
        """Execute simulation circuits and collect (ideal, noisy) results."""
        results_by_depth: Dict[int, List[Tuple[Dict[str, float], Dict[str, float]]]] = defaultdict(list)
        if engine is None:
            ideal_backend = IdealBackend()

            class _DummyBackend(BaseBackend):
                def run(self, circ, shots):
                    return None, {}

            engine = QuantumEngine(_DummyBackend())
            engine.ideal_backend = ideal_backend

        iterator = tqdm(circuits, disable=not (_TQDM_AVAILABLE and show_progress))
        all_results = engine.execute_with_ideal(iterator, shots=shots)
        for circ, (ideal, noisy) in zip(circuits, all_results):
            depth = circ.metadata["depth"]
            if self.reject_uniform_circuits:
                is_u, _ = self._is_uniform_distribution(ideal)
                if is_u:
                    continue
            results_by_depth[depth].append((ideal, noisy))
        return results_by_depth

    # ------------------------------------------------------------------
    def run(
        self,
        engine: Optional[QuantumEngine] = None,
        circuits: Optional[List[QuantumCircuit]] = None,
        shots: int = 2048,
        plot: bool = True,
        experimental_results: Optional[List[Dict[str, float]]] = None,
        experimental_data_by_depth: Optional[Dict[int, List[Dict[str, float]]]] = None,
        show_progress: bool = True,
        debug: bool = False,
        **plot_kwargs,
    ) -> Dict[str, Any]:
        """Unified entry point for SPB experiment."""
        circuits = circuits or self.circuits()
        mode = (
            "simulation"
            if engine is not None
            else "user_data"
            if (experimental_data_by_depth or experimental_results)
            else "simulation"
        )
        logger.info(f"[INFO] Starting Standard-SPB | mode={mode}")

        if mode == "simulation":
            results_by_depth = self._run_simulation_mode(engine, circuits, shots, show_progress)
        else:
            ideal_backend = IdealBackend()
            results_by_depth: Dict[int, List[Tuple[Dict[str, float], Dict[str, float]]]] = defaultdict(list)
            for idx, circ in enumerate(circuits):
                depth = circ.metadata.get("depth", 0)
                ideal_probs = ideal_backend.statevector_to_probs(ideal_backend.get_statevector(circ))
                data_list = []
                if experimental_data_by_depth and depth in experimental_data_by_depth:
                    data_list = experimental_data_by_depth[depth]
                elif experimental_results and idx < len(experimental_results):
                    data_list = [experimental_results[idx]]
                for noisy_dict in data_list:
                    results_by_depth[depth].append((ideal_probs, noisy_dict))

        # ------------------- Analysis -------------------
        purities_by_depth: Dict[int, List[float]] = {d: [] for d in sorted(results_by_depth.keys())}
        for d in purities_by_depth:
            for ideal, noisy in results_by_depth[d]:
                pval = analyze_speckle_purity(ideal, noisy, self.num_qubits)
                purities_by_depth[d].append(pval)
        fit = fit_spb_decay(list(purities_by_depth.keys()), purities_by_depth)
        self.results = {
            "purities_by_depth": purities_by_depth,
            "spb_fit": fit,
            "axis_mode": self.x_axis_mode,
        }

        if debug:
            logger.debug(f"SPB fit result: {fit}")

        if plot:
            self._plot_results(title=f"SPB on qubits {self.qubits}", **plot_kwargs)
        return self.results

    # ------------------------------------------------------------------
    def _plot_results(self, title: str, **kwargs):
        """Render SPB decay curve."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(7.5, 5.5))
        fig.suptitle(title, fontsize=14)
        plot_spb_decay(
            raw_data=self.results["purities_by_depth"],
            fit_results=self.results["spb_fit"],
            ax=ax,
            axis_mode=self.x_axis_mode,
            **kwargs,
        )
        ax.grid(True, linestyle="--", linewidth=0.5)
        plt.tight_layout(rect=[0, 0, 1, 0.94])
        plt.show()


# =============================================================================
# CLASS: Interleaved SPB Experiment
# =============================================================================
class InterleavedSPBExperiment(StandardSPBExperiment):
    """Perform Interleaved SPB to evaluate gate-specific purity decay."""

    def __init__(self, qubits: List[int], interleaved_gate: Gate, **kwargs):
        super().__init__(qubits, **kwargs)
        self.interleaved_gate = interleaved_gate

    # ------------------------------------------------------------------
    def _generate_reference_circuit(self, depth: int, seed: Optional[int]):
        return self._generate_circuit(depth, seed)

    def _generate_interleaved_circuit(self, depth: int, seed: Optional[int]):
        """Generate an interleaved SPB circuit for the given depth."""
        rng = random.Random(seed)
        circ = QuantumCircuit(self.qubits)
        if depth == 0:
            circ.measure_all()
            circ.metadata = {"depth": 0, "seed": seed, "mode": "interleaved"}
            return circ
        for _ in range(depth):
            circ.add_gates(self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random()))
            circ.add_gate(self.interleaved_gate)
        circ.add_gates(self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random()))
        circ.measure_all()
        circ.metadata = {"depth": depth, "seed": seed, "mode": "interleaved"}
        return circ

    # ------------------------------------------------------------------
    def circuits(self, mode: str = "interleaved") -> List[QuantumCircuit]:
        """Generate reference or interleaved circuits."""
        if self._circuits is not None:
            return self._circuits
        rng = random.Random(self.seed)
        circuits: List[QuantumCircuit] = []
        for d in self.depths:
            for _ in range(self.circuits_per_depth):
                if mode == "reference":
                    circuits.append(self.generate_single_circuit(d, rng.random()))
                else:
                    circuits.append(self.generate_single_circuit(d, rng.random()))
        self._circuits = circuits
        return circuits

    # ------------------------------------------------------------------
    def _run_simulation_mode(self, engine, circuits, shots, show_progress=True):
        """Wrapper to reuse StandardSPBExperiment simulation logic."""
        return super()._run_simulation_mode(engine, circuits, shots, show_progress)

    # ------------------------------------------------------------------
    def run(
        self,
        engine: Optional[QuantumEngine] = None,
        shots: int = 2048,
        show_progress: bool = True,
        plot: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run reference and interleaved SPB, compute gate-purity metrics."""
        logger.info(f"[INFO] Running Interleaved-SPB for gate '{self.interleaved_gate.name}'")

        circuits_ref = self.circuits(mode="reference")
        circuits_int = self.circuits(mode="interleaved")

        ref_res = self._run_simulation_mode(engine, circuits_ref, shots, show_progress)
        int_res = self._run_simulation_mode(engine, circuits_int, shots, show_progress)

        ref_analysis = self._analyze_results(ref_res)
        int_analysis = self._analyze_results(int_res)

        p_ref = ref_analysis["spb_fit"].get("p_c", 0)
        p_int = int_analysis["spb_fit"].get("p_c", 0)
        d = 2 ** len(self.interleaved_gate.qubits)

        ratio_raw = p_int / p_ref if p_ref != 0 else 0.0
        ratio = np.clip(ratio_raw, 0.0, 1.0)
        gate_error = (1 - ratio) * ((d**2 - 1) / d**2)
        gate_purity = 1 - gate_error

        self.results = {
            "reference": ref_analysis,
            "interleaved": int_analysis,
            "gate_purity": gate_purity,
            "gate_error": gate_error,
            "ratio_raw": ratio_raw,
            "ratio": ratio,
        }

        if plot:
            self._plot_interleaved()
        return self.results

    # ------------------------------------------------------------------
    def _analyze_results(self, res_dict: Dict[int, List[Tuple[Dict[str, float], Dict[str, float]]]]) -> Dict[str, Any]:
        """Analyze SPB results grouped by circuit depth."""
        purities_by_depth: Dict[int, List[float]] = {d: [] for d in sorted(res_dict.keys())}
        for d in purities_by_depth:
            for ideal, noisy in res_dict[d]:
                val = analyze_speckle_purity(ideal, noisy, self.num_qubits)
                purities_by_depth[d].append(val)
        fit = fit_spb_decay(list(purities_by_depth.keys()), purities_by_depth)
        return {"purities_by_depth": purities_by_depth, "spb_fit": fit}

    # ------------------------------------------------------------------
    def _plot_interleaved(self):
        """Plot comparison between reference and interleaved SPB results."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(7.5, 5.5))
        fig.suptitle(f"Interleaved SPB - {self.interleaved_gate.name}", fontsize=14)
        ref = self.results["reference"]
        inter = self.results["interleaved"]

        plot_spb_decay(
            raw_data=ref["purities_by_depth"],
            fit_results=ref["spb_fit"],
            ax=ax,
            color="#1f77b4",
            label="Reference",
        )
        plot_spb_decay(
            raw_data=inter["purities_by_depth"],
            fit_results=inter["spb_fit"],
            ax=ax,
            color="#d62728",
            label="Interleaved",
        )

        ax.legend(frameon=False)
        ax.grid(True, linestyle="--", linewidth=0.5)
        plt.tight_layout(rect=[0, 0, 1, 0.94])
        plt.show()