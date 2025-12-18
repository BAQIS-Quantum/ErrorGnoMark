# File: egm/core/experiments/benchmarking/xeb.py
# [v4.5 — Clean RB‑Style Separation of Concerns]
# ---------------------------------------------------------------------
# Cross‑Entropy Benchmarking (XEB) Experiment Definitions
# ---------------------------------------------------------------------
# Responsibilities:
#   • Circuit generation and execution orchestration
#   • Unified analysis of XEB (fidelity) and SPB (purity)
#   • Data aggregation per circuit depth
#   • Independent visualization through egm.reporting.visualizers.xeb_plotter
# ---------------------------------------------------------------------

from __future__ import annotations
import random
import numpy as np
import logging
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Optional, Union
from egm.core.circuits.circuit import QuantumCircuit, Gate
from egm.core.circuits.gate_sets import BaseGateSet, TwoQubitGateSet, get_gate_set
from egm.core.engine.executor import QuantumEngine
from egm.core.analysis.xeb import analyze_xeb_and_spb_from_results

# (Visualization functions are imported for external use, but not used internally)
from egm.reporting.visualizers.xeb_plotter import plot_xeb_decay, plot_spb_decay

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Default Parameters
# ---------------------------------------------------------------------
DEFAULT_DEPTHS = [0, 5, 10, 15, 25, 40, 60]
DEFAULT_NUM_CIRCUITS = 30
DEFAULT_NATIVE_GATES = ["cz", "sx", "rz", "h", "s"]


# ---------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------
def _validate_qubits(qubits: Any) -> None:
    """Verify that 'qubits' is a list or tuple of integers."""
    if not isinstance(qubits, (list, tuple)) or not all(isinstance(q, int) for q in qubits):
        raise TypeError("Parameter 'qubits' must be a list of integers.")


# =====================================================================
# CLASS: Standard XEB Experiment
# =====================================================================
class StandardXEBExperiment:
    """
    Implements the Standard Cross‑Entropy Benchmarking protocol.

    This class handles:
        • Circuit generation
        • Execution via QuantumEngine or user‑provided data
        • Combined analysis (XEB + SPB)
        • Optional data aggregation per depth
    """

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

        logger.info(f"Initialized Standard XEB on {self.num_qubits} qubits with depths {self.depths}")

    # -----------------------------------------------------------------
    def _default_topology(self) -> List[Tuple[int, int]]:
        """Return a simple linear nearest‑neighbor connectivity if not specified."""
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
        """Generate one randomized XEB circuit at a specific depth."""
        rng = random.Random(seed)
        circ = QuantumCircuit(qubits=self.qubits)

        # Depth == 0 yields identity circuit
        if depth == 0:
            circ.measure_all()
            circ.metadata.update({"depth": 0, "seed": seed})
            if interleaved_gate:
                circ.metadata["interleaved_gate_name"] = interleaved_gate.name
            return circ

        # Randomized layer construction
        pattern_a, pattern_b = self.topology[0::2], self.topology[1::2]
        for d in range(depth):
            circ.add_gates(self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random()))
            if self.topology and isinstance(self.gate_set_obj, TwoQubitGateSet):
                pattern = pattern_a if d % 2 == 0 else pattern_b
                circ.add_gates(self.gate_set_obj.get_random_2q_layer(pattern, seed=rng.random()))
            if interleaved_gate:
                circ.add_gate(interleaved_gate)

        # Final layer + measurement
        circ.add_gates(self.gate_set_obj.get_random_1q_layer(self.qubits, seed=rng.random()))
        circ.measure_all()

        circ.metadata.update({"depth": depth, "seed": seed})
        if interleaved_gate:
            circ.metadata["interleaved_gate_name"] = interleaved_gate.name
        return circ

    # -----------------------------------------------------------------
    def generate_single_circuit(
        self,
        depth: int,
        seed: Optional[Union[int, float]] = None,
        interleaved_gate: Optional[Gate] = None,
    ) -> QuantumCircuit:
        """Generate a single circuit and decompose to native basis if required."""
        circ = self._generate_circuit(depth, seed, interleaved_gate)
        if self.native_gates:
            circ = circ.decompose(basis_gates=self.native_gates)
        circ.metadata["noise_exponent"] = sum(1 for g in circ.gates if not g.is_measurement)
        return circ

    # -----------------------------------------------------------------
    def circuits(self) -> List[QuantumCircuit]:
        """Return or build all benchmark circuits."""
        if self._circuits is not None:
            return self._circuits
        rng = random.Random(self.seed)
        circuits = []
        for d in self.depths:
            for _ in range(self.circuits_per_depth):
                circuits.append(self.generate_single_circuit(d, rng.random()))
        self._circuits = circuits
        return circuits

    # -----------------------------------------------------------------
    # Aggregation
    # -----------------------------------------------------------------
    def _aggregate_results(
        self,
        raw_results: Dict[int, List[Tuple[Dict[str, float], Dict[str, float]]]],
    ) -> Dict[str, Dict[int, float]]:
        """
        Aggregate circuit-level results into mean values per depth
        for XEB fidelity and SPB purity.
        """
        fidelities_mean = {}
        purities_mean = {}
        for depth, samples in raw_results.items():
            fidelities = [np.mean(list(ideal.values())) for (ideal, _) in samples]
            purities = [np.mean(list(obs.values())) for (_, obs) in samples]
            fidelities_mean[depth] = np.mean(fidelities)
            purities_mean[depth] = np.mean(purities)
        return {"xeb_means": fidelities_mean, "spb_means": purities_mean}

    # -----------------------------------------------------------------
    # Execution & Analysis
    # -----------------------------------------------------------------
    def run(
        self,
        engine: QuantumEngine,
        shots: int = 2048,
        experimental_results: Optional[List[Any]] = None,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute or analyze a full XEB experiment.

        Returns:
            A dictionary containing raw data, fit results, and aggregated values.
        """
        mode = "User Data" if experimental_results else "Engine"
        logger.info(f"--- Running {self.num_qubits}‑Qubit XEB [{mode} Mode] ---")

        circuits = self.circuits()
        results_by_depth = defaultdict(list)

        # ----------------------------- User Data -----------------------------
        if experimental_results is not None:
            if len(experimental_results) != len(circuits):
                raise ValueError("Experimental results count mismatches circuit count.")
            for circ, exp_data in zip(circuits, experimental_results):
                depth = circ.metadata.get("depth")
                # detect tuple input (ideal, noisy)
                if isinstance(exp_data, tuple) and len(exp_data) == 2:
                    _, exp_data = exp_data
                    logger.info("[INFO] Detected (ideal, noisy) tuple; using noisy distribution.")
                total = sum(exp_data.values())
                exp_data = (
                    exp_data if abs(total - 1.0) < 1e-6 else {k: v / total for k, v in exp_data.items()}
                )
                ideal = engine._statevector_to_probs(
                    engine.get_ideal_statevector(circ), circ.num_qubits
                )
                results_by_depth[depth].append((ideal, exp_data))

        # ----------------------------- Engine Mode ----------------------------
        else:
            try:
                from tqdm import tqdm
                iterator = tqdm(circuits, disable=not show_progress, desc="Executing XEB Circuits")
            except ImportError:
                iterator = circuits
            all_results = engine.execute_with_ideal(iterator, shots)
            for circ, (ideal, noisy) in zip(circuits, all_results):
                results_by_depth[circ.metadata["depth"]].append((ideal, noisy))

        # -------------------------- Analysis ----------------------------------
        self.results = analyze_xeb_and_spb_from_results(results_by_depth, self.num_qubits)
        self.results["aggregated"] = self._aggregate_results(results_by_depth)

        logger.info("XEB run completed; analysis results ready.")
        return self.results


# =====================================================================
# CLASS: Interleaved XEB Experiment
# =====================================================================
class InterleavedXEBExperiment(StandardXEBExperiment):
    """
    Perform Interleaved XEB to estimate gate‑specific fidelity.
    """

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

    def circuits(self) -> List[QuantumCircuit]:
        """Generate the complete interleaved XEB circuit ensemble."""
        if self._circuits is not None:
            return self._circuits
        rng = random.Random(self.seed)
        circuits = [
            self.generate_single_circuit(d, rng.random(), interleaved_gate=self.interleaved_gate)
            for d in self.depths
            for _ in range(self.circuits_per_depth)
        ]
        self._circuits = circuits
        return circuits

    def run(
        self,
        engine: QuantumEngine,
        shots: int = 2048,
        experimental_results_ref: Optional[List[Any]] = None,
        experimental_results_int: Optional[List[Any]] = None,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """Run both standard reference and interleaved XEB sequences."""
        gate_name = self.interleaved_gate.name
        logger.info(f"--- Running Interleaved XEB for Gate '{gate_name}' ---")

        # 1. Reference (Standard) XEB
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
            experimental_results=experimental_results_ref,
            show_progress=show_progress,
        )

        # 2. Interleaved XEB
        int_res = super().run(
            engine=engine,
            shots=shots,
            experimental_results=experimental_results_int,
            show_progress=show_progress,
        )

        # 3. Compute gate fidelity metrics
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
        logger.info("Interleaved XEB analysis complete.")
        return self.results


# ---------------------------------------------------------------------
# End of File
# ---------------------------------------------------------------------