from __future__ import annotations

import logging
import random
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from egm.core.backends.base_backend import BaseBackend
from egm.core.backends.ideal_backend import IdealBackend
from egm.core.circuits.circuit import Gate, QuantumCircuit
from egm.core.circuits.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set
from egm.core.execution.executor import Executor
from egm.core.analysis.xeb import fit_xeb_data, analyze_xeb_and_spb_from_results
from egm.core.analysis.spb import fit_spb_data

logger = logging.getLogger(__name__)

DEFAULT_XEB_DEPTHS: List[int] = [0, 2, 4, 6, 8, 12, 20, 32, 40]
DEFAULT_CIRCUITS_PER_DEPTH: int = 10


# =============================================================================
# Utilities
# =============================================================================

def _default_topology(qubits: List[int]) -> List[Tuple[int, int]]:
    """Linear nearest-neighbor topology for a qubit list."""
    return list(zip(qubits, qubits[1:]))


def _is_uniform(
    probs: Dict[str, float],
    num_qubits: int,
    threshold: float = 0.999,
) -> bool:
    """Return True if the probability distribution is near-uniform."""
    vals = np.array(list(probs.values()), float)
    vals = vals[vals > 0]
    if len(vals) == 0:
        return True
    h = -np.sum(vals * np.log(vals))
    h_max = np.log(2 ** num_qubits)
    return (h / h_max) > threshold


def merge_xeb_circuits(circuits_list: List[QuantumCircuit]) -> QuantumCircuit:
    """
    Merge multiple disjoint XEB circuits into one simultaneous circuit.

    Gates from each sub-circuit (excluding measurements) are combined into
    a single circuit covering all qubits, with a single measure_all() at the end.
    """
    all_qubits: set = set()
    all_gates: List[Gate] = []
    meta_depth = None

    for qc in circuits_list:
        all_qubits.update(qc.qubits)
        all_gates.extend(g for g in qc.gates if not g.is_measurement)
        if meta_depth is None:
            meta_depth = qc.metadata.get("depth")

    merged = QuantumCircuit(qubits=sorted(list(all_qubits)), gates=all_gates)
    merged.measure_all()
    merged.metadata = {"depth": meta_depth, "mode": "simultaneous_merged"}
    return merged


# =============================================================================
# Level 1: Core Kernel (pure logic)
# =============================================================================

def _generate_xeb_circuit(
    qubits: List[int],
    depth: int,
    gate_set_obj: BaseGateSet,
    topology: List[Tuple[int, int]],
    seed: Optional[float] = None,
    interleaved_gate: Optional[Gate] = None,
    native_gates: Optional[List[str]] = None,
) -> QuantumCircuit:
    """
    Internal kernel: generate a single randomized XEB circuit.

    Alternates 1Q random layers with 2Q entangling layers following the
    provided topology, optionally interleaving a target gate between layers.
    """
    rng = random.Random(seed)
    circ = QuantumCircuit(qubits=qubits)

    if depth == 0:
        circ.measure_all()
        circ.metadata.update({"depth": 0, "seed": seed})
        return circ

    pattern_a = topology[0::2]
    pattern_b = topology[1::2]

    for d in range(depth):
        circ.add_gates(gate_set_obj.get_random_1q_layer(qubits, seed=rng.random()))
        if topology and isinstance(gate_set_obj, TwoQubitGateSet):
            pairs = pattern_a if d % 2 == 0 else pattern_b
            circ.add_gates(gate_set_obj.get_random_2q_layer(pairs, seed=rng.random()))
        if interleaved_gate:
            circ.add_gate(interleaved_gate)

    circ.add_gates(gate_set_obj.get_random_1q_layer(qubits, seed=rng.random()))
    circ.measure_all()
    circ.metadata.update({
        "depth": depth,
        "gate_count": sum(1 for g in circ.gates if not g.is_measurement),
        "seed": seed,
    })

    if native_gates:
        try:
            circ = circ.decompose(basis_gates=native_gates)
        except Exception as e:
            logger.warning("Decomposition failed at depth=%d: %s", depth, e)

    return circ


# =============================================================================
# Level 2: Single Circuit Wrappers
# =============================================================================

def generate_single_standard_xeb_circuit(
    qubits: List[int],
    depth: int,
    gate_set: Union[str, BaseGateSet] = "sycamore_xeb",
    topology: Optional[List[Tuple[int, int]]] = None,
    seed: Optional[float] = None,
    native_gates: Optional[List[str]] = None,
) -> QuantumCircuit:
    """Level 2: Generate a single standard XEB circuit."""
    gate_set_obj = get_gate_set(gate_set) if isinstance(gate_set, str) else gate_set
    topo = topology or _default_topology(qubits)
    return _generate_xeb_circuit(qubits, depth, gate_set_obj, topo, seed,
                                 native_gates=native_gates)


def generate_single_interleaved_xeb_circuit(
    qubits: List[int],
    depth: int,
    interleaved_gate: Gate,
    gate_set: Union[str, BaseGateSet] = "sycamore_xeb",
    topology: Optional[List[Tuple[int, int]]] = None,
    seed: Optional[float] = None,
    native_gates: Optional[List[str]] = None,
) -> QuantumCircuit:
    """Level 2: Generate a single interleaved XEB circuit."""
    if interleaved_gate is None:
        raise ValueError("Interleaved XEB requires a valid 'interleaved_gate'.")
    gate_set_obj = get_gate_set(gate_set) if isinstance(gate_set, str) else gate_set
    topo = topology or _default_topology(qubits)
    return _generate_xeb_circuit(qubits, depth, gate_set_obj, topo, seed,
                                 interleaved_gate=interleaved_gate,
                                 native_gates=native_gates)


# =============================================================================
# Level 3: Batch & Orchestration
# =============================================================================

# ---------------------------------------------------------------------------
# A. Standard XEB Family
# ---------------------------------------------------------------------------

def generate_standard_xeb_circuits(
    qubits: List[int],
    depths: List[int],
    circuits_per_depth: int,
    gate_set: Union[str, BaseGateSet] = "sycamore_xeb",
    topology: Optional[List[Tuple[int, int]]] = None,
    seed: Optional[int] = None,
    native_gates: Optional[List[str]] = None,
    reject_uniform_circuits: bool = True,
    entropy_threshold: float = 0.999,
    max_attempts_multiplier: int = 10,
) -> List[QuantumCircuit]:
    """
    Level 3: Generate a batch of standard XEB circuits.

    Args:
        qubits: Target qubit indices.
        depths: List of circuit depths to generate.
        circuits_per_depth: Number of random circuits per depth.
        gate_set: Gate set identifier or BaseGateSet instance.
        topology: Qubit connectivity. Defaults to linear chain.
        seed: Master seed for reproducibility.
        native_gates: Decompose into these basis gates if provided.
        reject_uniform_circuits: Discard near-uniform circuits via ideal simulation.
        entropy_threshold: Normalized entropy above which a circuit is rejected.
        max_attempts_multiplier: Max retries = multiplier × circuits_per_depth.

    Returns:
        Flat list of QuantumCircuit objects across all depths.
    """
    gate_set_obj = get_gate_set(gate_set) if isinstance(gate_set, str) else gate_set
    topo = topology or _default_topology(qubits)
    num_qubits = len(qubits)
    rng = random.Random(seed)
    ideal_backend = IdealBackend() if reject_uniform_circuits else None
    all_circuits: List[QuantumCircuit] = []

    for depth in depths:
        valids: List[QuantumCircuit] = []
        attempts = 0
        max_attempts = max_attempts_multiplier * circuits_per_depth

        while len(valids) < circuits_per_depth and attempts < max_attempts:
            attempts += 1
            c = _generate_xeb_circuit(qubits, depth, gate_set_obj, topo,
                                      rng.random(), native_gates=native_gates)
            if reject_uniform_circuits and depth > 0 and ideal_backend is not None:
                try:
                    sv = ideal_backend.get_statevector(c)
                    probs = ideal_backend.statevector_to_probs(sv)
                    if _is_uniform(probs, num_qubits, entropy_threshold):
                        continue
                except Exception:
                    pass
            valids.append(c)

        all_circuits.extend(valids)
        logger.debug("depth=%d: accepted %d / attempted %d", depth, len(valids), attempts)

    return all_circuits


def generate_respectively_standard_xeb_circuits(
    qubit_groups: List[List[int]],
    depths: List[int],
    circuits_per_depth: int,
    gate_set: Union[str, BaseGateSet] = "sycamore_xeb",
    topologies: Optional[List[List[Tuple[int, int]]]] = None,
    seed: Optional[int] = None,
    native_gates: Optional[List[str]] = None,
    reject_uniform_circuits: bool = True,
    entropy_threshold: float = 0.999,
    max_attempts_multiplier: int = 10,
) -> Dict[Tuple[int, ...], List[QuantumCircuit]]:
    """
    Level 3: Generate independent standard XEB circuit batches for multiple qubit groups.

    Each group runs its own separate experiment (different shots / jobs).
    Circuits are generated with zero-based local qubit indices; original physical
    qubit labels are stored in each circuit's metadata as ``original_qubits``.

    Returns:
        Dict mapping qubit group tuple to list of circuits.
    """
    results: Dict[Tuple[int, ...], List[QuantumCircuit]] = {}
    for i, group in enumerate(qubit_groups):
        # Remap to local 0-based indices so simulation backends always receive
        # contiguous qubit indices regardless of physical qubit labels.
        local_qubits = list(range(len(group)))
        topo = topologies[i] if topologies else None
        group_seed = (seed + i * 1000) if seed is not None else None
        circs = generate_standard_xeb_circuits(
            qubits=local_qubits,
            depths=depths,
            circuits_per_depth=circuits_per_depth,
            gate_set=gate_set,
            topology=topo,
            seed=group_seed,
            native_gates=native_gates,
            reject_uniform_circuits=reject_uniform_circuits,
            entropy_threshold=entropy_threshold,
            max_attempts_multiplier=max_attempts_multiplier,
        )
        for c in circs:
            c.metadata["original_qubits"] = list(group)
        results[tuple(group)] = circs
    return results


def generate_simultaneously_standard_xeb_circuits(
    qubit_groups: List[List[int]],
    depths: List[int],
    circuits_per_depth: int,
    gate_set: Union[str, BaseGateSet] = "sycamore_xeb",
    topologies: Optional[List[List[Tuple[int, int]]]] = None,
    seed: Optional[int] = None,
    native_gates: Optional[List[str]] = None,
    reject_uniform_circuits: bool = True,
    entropy_threshold: float = 0.999,
    max_attempts_multiplier: int = 10,
) -> Dict[int, List[QuantumCircuit]]:
    """
    Level 3: Generate standard XEB circuits for all qubit groups to run simultaneously.

    Circuits for each depth slot are merged into a single circuit covering all qubits,
    enabling cross-talk characterization across disjoint qubit groups.

    Returns:
        Dict mapping depth to list of merged circuits.
    """
    gate_set_obj = get_gate_set(gate_set) if isinstance(gate_set, str) else gate_set
    rng = random.Random(seed)
    circuits_by_depth: Dict[int, List[QuantumCircuit]] = {d: [] for d in depths}

    for depth in depths:
        for _ in range(circuits_per_depth):
            sub_circuits = []
            for j, group in enumerate(qubit_groups):
                topo = topologies[j] if topologies else _default_topology(group)
                c = _generate_xeb_circuit(group, depth, gate_set_obj, topo,
                                          rng.random(), native_gates=native_gates)
                sub_circuits.append(c)
            merged = merge_xeb_circuits(sub_circuits)
            circuits_by_depth[depth].append(merged)

    return circuits_by_depth


# ---------------------------------------------------------------------------
# B. Interleaved XEB Family
# ---------------------------------------------------------------------------

def generate_interleaved_xeb_circuits(
    qubits: List[int],
    depths: List[int],
    circuits_per_depth: int,
    interleaved_gate: Gate,
    gate_set: Union[str, BaseGateSet] = "sycamore_xeb",
    topology: Optional[List[Tuple[int, int]]] = None,
    seed: Optional[int] = None,
    native_gates: Optional[List[str]] = None,
    reject_uniform_circuits: bool = True,
    entropy_threshold: float = 0.999,
    max_attempts_multiplier: int = 10,
) -> List[QuantumCircuit]:
    """Level 3: Generate a batch of interleaved XEB circuits."""
    gate_set_obj = get_gate_set(gate_set) if isinstance(gate_set, str) else gate_set
    topo = topology or _default_topology(qubits)
    num_qubits = len(qubits)
    rng = random.Random(seed)
    ideal_backend = IdealBackend() if reject_uniform_circuits else None
    all_circuits: List[QuantumCircuit] = []

    for depth in depths:
        valids: List[QuantumCircuit] = []
        attempts = 0
        max_attempts = max_attempts_multiplier * circuits_per_depth

        while len(valids) < circuits_per_depth and attempts < max_attempts:
            attempts += 1
            c = _generate_xeb_circuit(qubits, depth, gate_set_obj, topo,
                                      rng.random(),
                                      interleaved_gate=interleaved_gate,
                                      native_gates=native_gates)
            if reject_uniform_circuits and depth > 0 and ideal_backend is not None:
                try:
                    sv = ideal_backend.get_statevector(c)
                    probs = ideal_backend.statevector_to_probs(sv)
                    if _is_uniform(probs, num_qubits, entropy_threshold):
                        continue
                except Exception:
                    pass
            valids.append(c)

        all_circuits.extend(valids)

    return all_circuits


def generate_respectively_interleaved_xeb_circuits(
    qubit_groups: List[List[int]],
    depths: List[int],
    circuits_per_depth: int,
    interleaved_gate: Gate,
    gate_set: Union[str, BaseGateSet] = "sycamore_xeb",
    topologies: Optional[List[List[Tuple[int, int]]]] = None,
    seed: Optional[int] = None,
    native_gates: Optional[List[str]] = None,
    reject_uniform_circuits: bool = True,
    entropy_threshold: float = 0.999,
    max_attempts_multiplier: int = 10,
) -> Dict[Tuple[int, ...], List[QuantumCircuit]]:
    """Level 3: Generate independent interleaved XEB circuit batches for multiple qubit groups."""
    results: Dict[Tuple[int, ...], List[QuantumCircuit]] = {}
    for i, group in enumerate(qubit_groups):
        topo = topologies[i] if topologies else None
        group_seed = (seed + i * 1000) if seed is not None else None
        results[tuple(group)] = generate_interleaved_xeb_circuits(
            qubits=group,
            depths=depths,
            circuits_per_depth=circuits_per_depth,
            interleaved_gate=interleaved_gate,
            gate_set=gate_set,
            topology=topo,
            seed=group_seed,
            native_gates=native_gates,
            reject_uniform_circuits=reject_uniform_circuits,
            entropy_threshold=entropy_threshold,
            max_attempts_multiplier=max_attempts_multiplier,
        )
    return results


def generate_simultaneously_interleaved_xeb_circuits(
    qubit_groups: List[List[int]],
    depths: List[int],
    circuits_per_depth: int,
    interleaved_gate: Gate,
    gate_set: Union[str, BaseGateSet] = "sycamore_xeb",
    topologies: Optional[List[List[Tuple[int, int]]]] = None,
    seed: Optional[int] = None,
    native_gates: Optional[List[str]] = None,
    reject_uniform_circuits: bool = True,
    entropy_threshold: float = 0.999,
    max_attempts_multiplier: int = 10,
) -> Dict[int, List[QuantumCircuit]]:
    """Level 3: Generate interleaved XEB circuits for all qubit groups to run simultaneously."""
    gate_set_obj = get_gate_set(gate_set) if isinstance(gate_set, str) else gate_set
    rng = random.Random(seed)
    circuits_by_depth: Dict[int, List[QuantumCircuit]] = {d: [] for d in depths}

    for depth in depths:
        for _ in range(circuits_per_depth):
            sub_circuits = []
            for j, group in enumerate(qubit_groups):
                topo = topologies[j] if topologies else _default_topology(group)
                c = _generate_xeb_circuit(group, depth, gate_set_obj, topo,
                                          rng.random(),
                                          interleaved_gate=interleaved_gate,
                                          native_gates=native_gates)
                sub_circuits.append(c)
            merged = merge_xeb_circuits(sub_circuits)
            circuits_by_depth[depth].append(merged)

    return circuits_by_depth


# =============================================================================
# Class API
# =============================================================================

class StandardXEBExperiment:
    """
    Standard Cross-Entropy Benchmarking experiment.

    Wraps circuit generation, execution, and analysis into a single object.
    Delegates circuit generation to the module-level free functions.
    """

    def __init__(
        self,
        qubits: List[int],
        depths: List[int] = DEFAULT_XEB_DEPTHS,
        circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
        gate_set: Union[str, BaseGateSet] = "sycamore_xeb",
        seed: Optional[int] = None,
        native_gates: Optional[List[str]] = None,
        topology: Optional[List[Tuple[int, int]]] = None,
        reject_uniform_circuits: bool = True,
        entropy_threshold: float = 0.999,
        max_attempts_multiplier: int = 10,
        x_axis_mode: str = "depth",
    ):
        self.qubits = list(qubits)
        self.num_qubits = len(qubits)
        self.depths = list(depths)
        self.circuits_per_depth = circuits_per_depth
        self.gate_set = gate_set
        self.seed = seed
        self.native_gates = native_gates
        self.topology = topology or _default_topology(qubits)
        self.reject_uniform_circuits = reject_uniform_circuits
        self.entropy_threshold = entropy_threshold
        self.max_attempts_multiplier = max_attempts_multiplier
        self.x_axis_mode = x_axis_mode

        self._circuits: Optional[List[QuantumCircuit]] = None
        self.results: Dict[str, Any] = {}

    def circuits(self) -> List[QuantumCircuit]:
        """Generate and cache all XEB circuits."""
        if self._circuits is None:
            self._circuits = generate_standard_xeb_circuits(
                qubits=self.qubits,
                depths=self.depths,
                circuits_per_depth=self.circuits_per_depth,
                gate_set=self.gate_set,
                topology=self.topology,
                seed=self.seed,
                native_gates=self.native_gates,
                reject_uniform_circuits=self.reject_uniform_circuits,
                entropy_threshold=self.entropy_threshold,
                max_attempts_multiplier=self.max_attempts_multiplier,
            )
        return self._circuits

    def run(
        self,
        executor: Executor,
        shots: int = 2048,
        plot: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute circuits and run XEB + SPB analysis.

        Args:
            executor: Executor instance wrapping the noisy backend.
            shots: Shots per circuit.
            plot: If True, display decay plots.

        Returns:
            Dict with 'xeb_analysis', 'spb_analysis', 'xeb_fit', 'spb_fit'.
        """
        circuits = self.circuits()
        logger.info("XEB: executing %d circuits on %d qubits.", len(circuits), self.num_qubits)

        all_results = executor.execute_with_ideal(circuits, shots=shots)

        results_by_depth: Dict[int, list] = defaultdict(list)
        for circ, (ideal, noisy) in zip(circuits, all_results):
            depth = circ.metadata.get("depth", 0)
            if ideal and self.reject_uniform_circuits:
                if _is_uniform(ideal, self.num_qubits, self.entropy_threshold):
                    continue
            results_by_depth[depth].append((ideal, noisy))

        analysis = analyze_xeb_and_spb_from_results(
            results_by_depth,
            num_qubits=self.num_qubits,
            axis_mode=self.x_axis_mode,
        )
        self.results = {
            **analysis,
            "xeb_fit": analysis["xeb_analysis"]["fit_results"],
            "spb_fit": analysis["spb_analysis"]["fit_results"],
        }

        xeb_fit = self.results["xeb_fit"]
        logger.info(
            "XEB fit: p=%.5f, EPC=%.3e, R²=%.4f",
            xeb_fit.get("p", float("nan")),
            xeb_fit.get("epc", float("nan")),
            xeb_fit.get("r_squared", float("nan")),
        )

        if plot:
            self._plot()

        return self.results

    def _plot(self):
        import matplotlib.pyplot as plt
        from egm.reporting.visualizers.xeb_plotter import plot_xeb_decay
        from egm.reporting.visualizers.spb_plotter import plot_spb_decay

        fig, (ax_xeb, ax_spb) = plt.subplots(2, 1, figsize=(6.4, 5.8), sharex=True)
        fig.suptitle(f"XEB on qubits {self.qubits}", fontsize=12)
        plot_xeb_decay(
            raw_data=self.results["xeb_analysis"]["raw_data"],
            fit_results=self.results["xeb_analysis"]["fit_results"],
            ax=ax_xeb, axis_mode=self.x_axis_mode, show=False,
        )
        plot_spb_decay(
            raw_data=self.results["spb_analysis"]["raw_data"],
            fit_results=self.results["spb_analysis"]["fit_results"],
            ax=ax_spb, axis_mode=self.x_axis_mode, show=False,
        )
        ax_xeb.set_ylabel("Mean XEB Fidelity")
        ax_spb.set_ylabel("Mean State Purity")
        ax_spb.set_xlabel("Depth")
        for ax in (ax_xeb, ax_spb):
            ax.grid(True, linestyle="--", linewidth=0.6)
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()


class InterleavedXEBExperiment(StandardXEBExperiment):
    """
    Interleaved Cross-Entropy Benchmarking experiment.

    Runs both a reference (standard) and interleaved batch, then computes
    the per-gate error from the ratio of their fitted decay parameters.
    """

    def __init__(
        self,
        qubits: List[int],
        interleaved_gate: Gate,
        **kwargs,
    ):
        super().__init__(qubits, **kwargs)
        self.interleaved_gate = interleaved_gate
        self._circuits_ref: Optional[List[QuantumCircuit]] = None
        self._circuits_int: Optional[List[QuantumCircuit]] = None

    def circuits(self, mode: str = "interleaved") -> List[QuantumCircuit]:
        """Generate reference or interleaved circuits (cached separately)."""
        if mode == "reference":
            if self._circuits_ref is None:
                self._circuits_ref = generate_standard_xeb_circuits(
                    qubits=self.qubits,
                    depths=self.depths,
                    circuits_per_depth=self.circuits_per_depth,
                    gate_set=self.gate_set,
                    topology=self.topology,
                    seed=self.seed,
                    native_gates=self.native_gates,
                    reject_uniform_circuits=self.reject_uniform_circuits,
                    entropy_threshold=self.entropy_threshold,
                    max_attempts_multiplier=self.max_attempts_multiplier,
                )
            return self._circuits_ref
        else:
            if self._circuits_int is None:
                self._circuits_int = generate_interleaved_xeb_circuits(
                    qubits=self.qubits,
                    depths=self.depths,
                    circuits_per_depth=self.circuits_per_depth,
                    interleaved_gate=self.interleaved_gate,
                    gate_set=self.gate_set,
                    topology=self.topology,
                    seed=self.seed,
                    native_gates=self.native_gates,
                    reject_uniform_circuits=self.reject_uniform_circuits,
                    entropy_threshold=self.entropy_threshold,
                    max_attempts_multiplier=self.max_attempts_multiplier,
                )
            return self._circuits_int

    def run(
        self,
        executor: Executor,
        shots: int = 2048,
        plot: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute reference and interleaved batches, compute gate fidelity.

        Returns:
            Dict with 'reference', 'interleaved', 'gate_fidelity', 'gate_error'.
        """
        circuits_ref = self.circuits("reference")
        circuits_int = self.circuits("interleaved")

        logger.info("IXEB: executing reference batch (%d circuits).", len(circuits_ref))
        ref_results = self._collect_results(executor, circuits_ref, shots)

        logger.info("IXEB: executing interleaved batch (%d circuits).", len(circuits_int))
        int_results = self._collect_results(executor, circuits_int, shots)

        ref_analysis = analyze_xeb_and_spb_from_results(
            ref_results, num_qubits=self.num_qubits, axis_mode=self.x_axis_mode
        )
        int_analysis = analyze_xeb_and_spb_from_results(
            int_results, num_qubits=self.num_qubits, axis_mode=self.x_axis_mode
        )

        p_ref = ref_analysis["xeb_analysis"]["fit_results"].get("p", 0.0)
        p_int = int_analysis["xeb_analysis"]["fit_results"].get("p", 0.0)

        d = 2 ** len(self.interleaved_gate.qubits)
        ratio = float(np.clip(p_int / p_ref if p_ref != 0 else 0.0, 0, 1))
        gate_error = (d - 1) / d * (1 - ratio)
        gate_fidelity = 1 - gate_error

        self.results = {
            "reference": ref_analysis,
            "interleaved": int_analysis,
            "gate_fidelity": gate_fidelity,
            "gate_error": gate_error,
            "p_ref": p_ref,
            "p_int": p_int,
            "ratio": ratio,
        }

        logger.info(
            "IXEB: gate_fidelity=%.6f, gate_error=%.3e", gate_fidelity, gate_error
        )

        if plot:
            self._plot_interleaved()

        return self.results

    def _collect_results(
        self,
        executor: Executor,
        circuits: List[QuantumCircuit],
        shots: int,
    ) -> Dict[int, list]:
        """Execute circuits and group (ideal, noisy) pairs by depth."""
        all_results = executor.execute_with_ideal(circuits, shots=shots)
        results_by_depth: Dict[int, list] = defaultdict(list)
        for circ, (ideal, noisy) in zip(circuits, all_results):
            depth = circ.metadata.get("depth", 0)
            if ideal and self.reject_uniform_circuits:
                if _is_uniform(ideal, self.num_qubits, self.entropy_threshold):
                    continue
            results_by_depth[depth].append((ideal, noisy))
        return results_by_depth

    def _plot_interleaved(self):
        import matplotlib.pyplot as plt
        from egm.reporting.visualizers.xeb_plotter import plot_xeb_decay
        from egm.reporting.visualizers.spb_plotter import plot_spb_decay

        ref = self.results["reference"]
        inter = self.results["interleaved"]
        fig, (ax_xeb, ax_spb) = plt.subplots(2, 1, figsize=(8.0, 6.0), sharex=True)
        fig.suptitle(
            f"Interleaved XEB — {self.interleaved_gate.name} "
            f"(fidelity={self.results['gate_fidelity']:.4f})",
            fontsize=12,
        )
        for analysis, label, color in [
            (ref, "Reference", "#1f77b4"),
            (inter, "Interleaved", "#ff7f0e"),
        ]:
            plot_xeb_decay(
                raw_data=analysis["xeb_analysis"]["raw_data"],
                fit_results=analysis["xeb_analysis"]["fit_results"],
                ax=ax_xeb, axis_mode=self.x_axis_mode,
                color=color, show=False,
            )
            plot_spb_decay(
                raw_data=analysis["spb_analysis"]["raw_data"],
                fit_results=analysis["spb_analysis"]["fit_results"],
                ax=ax_spb, axis_mode=self.x_axis_mode,
                color=color, show=False,
            )
        ax_xeb.set_ylabel("Mean XEB Fidelity")
        ax_xeb.legend(["Reference", "Interleaved"], frameon=False)
        ax_spb.set_ylabel("Mean State Purity")
        ax_spb.set_xlabel("Depth")
        for ax in (ax_xeb, ax_spb):
            ax.grid(True, linestyle="--", linewidth=0.6)
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()


# ---------------------------------------------------------------------------
# TODO: 迁移清单
# 完成后将所有调用方的 import 从旧路径更新：
#   from egm.core.experiments.physical.benchmarking.xeb import (
#       generate_single_standard_xeb_circuit,
#       generate_standard_xeb_circuits,
#       StandardXEBExperiment,
#       InterleavedXEBExperiment,
#   )
# ---------------------------------------------------------------------------
