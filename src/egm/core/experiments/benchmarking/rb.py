# =============================================================================
# File    : src/egm/core/experiments/benchmarking/rb.py
# Version : v5.4 - Unified Standard/Interleaved/Purity RB (EGM + SISQ Compatible + Modular PRB)
# Author  : OpenAI-Assistant
# =============================================================================
"""
Randomized Benchmarking (RB) Experiments - Unified Controller

Implements Standard, Interleaved, and Purity RB workflows with:
    • Clifford-based circuit generation
    • Engine or user-data execution modes
    • RB + PRB analysis integration (via prb.compute_purity_from_counts)
    • Optional dual-plot visualization
    • Debug-mode diagnostic outputs
"""

from __future__ import annotations
import random
import logging
from typing import List, Dict, Optional, Union, Tuple, Protocol, Any

import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Internal Imports
# ---------------------------------------------------------------------
from egm.core.circuits.circuit import QuantumCircuit, Gate
from egm.core.engine.executor import QuantumEngine
from egm.core.analysis.rb import fit_rb_data, calculate_epg
from egm.core.analysis.prb import (
    fit_prb_data,
    calculate_prb_gate_error,
    compute_purity_from_counts,  # replaces old _compute_purity
)
from egm.reporting.visualizers.rb_plotter import (
    plot_rb_data as plot_rb_single,
    plot_rb_comparison,
)
from egm.reporting.visualizers.prb_plotter import (
    plot_prb_single,
    plot_prb_comparison,
)
from egm.core.circuits.gate_sets import CliffordGateSet, get_gate_set

# ---------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# ---------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------
DEFAULT_RB_DEPTHS: List[int] = [0, 2, 4, 8, 12, 20, 32, 48, 64]
DEFAULT_CIRCUITS_PER_DEPTH: int = 25


# ---------------------------------------------------------------------
# CliffordFactory Protocol
# ---------------------------------------------------------------------
class CliffordFactory(Protocol):
    """Interface for Clifford circuit generation."""

    def get_random_clifford_and_inverse(
        self, qubits: List[int], seed: Optional[Union[int, float]]
    ) -> Tuple[List[Gate], List[Gate]]:
        ...


# =============================================================================
# Standard Randomized Benchmarking Experiment
# =============================================================================
class StandardRBExperiment:
    """
    Standard RB experiment controller supporting:
      - RB + PRB analysis
      - Engine simulation / user data
      - Debug mode and plotting
    """

    def __init__(
        self,
        qubits: Union[int, List[int]],
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
        native_gates: Optional[List[str]] = None,
        seed: Optional[Union[int, float]] = None,
        clifford_factory: Optional[Union[CliffordFactory, str]] = None,
        x_axis_mode: str = "GATE_COUNT",
    ):
        self.qubits = [qubits] if isinstance(qubits, int) else qubits
        self.num_qubits = len(self.qubits)
        self.depths = depths or DEFAULT_RB_DEPTHS
        self.circuits_per_depth = circuits_per_depth
        self.native_gates = native_gates
        self.seed = seed
        self.x_axis_mode = x_axis_mode.upper()
        if self.x_axis_mode not in ["DEPTH", "GATE_COUNT"]:
            raise ValueError("x_axis_mode must be 'DEPTH' or 'GATE_COUNT'.")

        # Factory auto-resolve
        if clifford_factory is None:
            clifford_factory = CliffordGateSet()
        elif isinstance(clifford_factory, str):
            if clifford_factory.lower() in ["rb_universal", "rb_clifford"]:
                clifford_factory = CliffordGateSet()
            else:
                clifford_factory = get_gate_set(clifford_factory)
        self.clifford_factory = clifford_factory
        self.results: Dict[str, Any] = {}

        logging.info(
            f"[RB-Init] {self.num_qubits}Q RB initialized "
            f"(x_axis={self.x_axis_mode}, native={'ON' if native_gates else 'OFF'})"
        )

    # -------------------------------------------------------------------------
    def _generate_circuit(
        self,
        depth: int,
        seed: Optional[Union[int, float]],
        interleaved_gate: Optional[Gate] = None,
    ) -> QuantumCircuit:
        """Generate a single RB sequence circuit."""
        rng = random.Random(seed)
        circ = QuantumCircuit(qubits=self.qubits)

        if depth == 0:
            circ.measure_all()
            circ.metadata.update({"depth": 0, "gate_count": 0, "seed": seed})
            return circ

        inv_seq = []
        for _ in range(depth):
            fwd, inv = self.clifford_factory.get_random_clifford_and_inverse(
                self.qubits, rng.random()
            )
            circ.add_gates(fwd)
            if interleaved_gate:
                circ.add_gate(interleaved_gate)
            inv_seq.append(inv)

        for invs in reversed(inv_seq):
            circ.add_gates(invs)

        circ.measure_all()
        circ.metadata.update(
            {"depth": depth, "gate_count": len(circ.gates), "seed": seed}
        )
        return circ

    def generate_single_circuit(
        self, depth: int, seed: Optional[Union[int, float]] = None
    ) -> QuantumCircuit:
        """Return one RB circuit (decomposed if native_gates provided)."""
        circ = self._generate_circuit(
            depth, seed, getattr(self, "interleaved_gate", None)
        )
        if self.native_gates:
            circ = circ.decompose(basis_gates=self.native_gates)
        return circ

    def circuits(self) -> List[QuantumCircuit]:
        """Generate the full set of RB circuits."""
        rng = random.Random(self.seed)
        all_circuits = []
        for d in self.depths:
            for _ in range(self.circuits_per_depth):
                all_circuits.append(self.generate_single_circuit(d, rng.random()))
        return all_circuits

    # -------------------------------------------------------------------------
    def run(
        self,
        circuits: Optional[List[QuantumCircuit]] = None,
        engine: Optional[QuantumEngine] = None,
        shots: int = 2048,
        plot: bool = True,
        experimental_results: Optional[List[Dict[str, float]]] = None,
        experimental_data_by_depth: Optional[Dict[int, List[Dict[str, float]]]] = None,
        debug: bool = False,
    ) -> Dict[str, Any]:
        """Execute RB + PRB analysis in unified workflow."""
        rb_type = (
            "Interleaved" if isinstance(self, InterleavedRBExperiment) else "Standard"
        )
        if circuits is None:
            circuits = self.circuits()
        mode = (
            "Engine"
            if engine
            else ("User-Data-Flat" if experimental_results else "User-Data-ByDepth")
        )
        logging.info(
            f"=== Running {rb_type} RB [{mode}] with {len(circuits)} circuits ==="
        )

        ground = "0" * self.num_qubits
        survivals: Dict[int, List[float]] = {d: [] for d in self.depths}
        purities: Dict[int, List[float]] = {d: [] for d in self.depths}
        gate_counts_avg: Dict[int, float] = {d: 0.0 for d in self.depths}

        # Acquire data
        if experimental_data_by_depth:
            for circ in circuits:
                d = circ.metadata["depth"]
                gate_counts_avg[d] += circ.metadata.get("gate_count", 0)
                for dat in experimental_data_by_depth.get(d, []):
                    total = sum(dat.values())
                    if total > 0:
                        p0 = dat.get(ground, 0) / total
                        survivals[d].append(p0)
                        purities[d].append(
                            compute_purity_from_counts(dat, self.num_qubits)
                        )
                        if debug:
                            print(
                                f"[DEBUG] depth={d}, survival={p0:.5f}, "
                                f"purity={purities[d][-1]:.5f}"
                            )

        elif experimental_results:
            if len(experimental_results) != len(circuits):
                raise ValueError(
                    "Mismatch between experimental_results and circuits."
                )
            for circ, dat in zip(circuits, experimental_results):
                if isinstance(dat, tuple) and len(dat) == 2:
                    _, dat = dat
                if not isinstance(dat, dict):
                    raise TypeError(
                        f"Unexpected data type for experimental result: {type(dat)}"
                    )
                d = circ.metadata["depth"]
                gate_counts_avg[d] += circ.metadata.get("gate_count", 0)
                t = sum(dat.values())
                if t > 0:
                    p0 = dat.get(ground, 0) / t
                    survivals[d].append(p0)
                    purities[d].append(
                        compute_purity_from_counts(dat, self.num_qubits)
                    )
                    if debug:
                        print(
                            f"[DEBUG] depth={d}, survival={p0:.5f}, "
                            f"purity={purities[d][-1]:.5f}"
                        )

        elif engine:
            res = engine.execute_with_ideal(circuits, shots=shots)
            for circ, (_, counts) in zip(circuits, res):
                d = circ.metadata["depth"]
                gate_counts_avg[d] += circ.metadata.get("gate_count", 0)
                p0 = counts.get(ground, 0) / shots
                survivals[d].append(p0)
                purities[d].append(
                    compute_purity_from_counts(counts, self.num_qubits)
                )
                if debug:
                    print(
                        f"[DEBUG] depth={d}, survival={p0:.5f}, "
                        f"purity={purities[d][-1]:.5f}"
                    )
        else:
            raise ValueError("Must supply either engine or experimental data.")

        # Normalize average gate counts
        for d in self.depths:
            n = max(len(survivals[d]), 1)
            gate_counts_avg[d] /= n

        # Fit RB and PRB curves
        rb_fit = fit_rb_data(
            survivals=survivals, num_qubits=self.num_qubits, gate_counts=gate_counts_avg
        )
        prb_fit = fit_prb_data(purities=purities, num_qubits=self.num_qubits)
        self.results = {"rb_fit": rb_fit, "prb_fit": prb_fit}

        if debug:
            print("[DEBUG] RB Fit:", rb_fit)
            print("[DEBUG] PRB Fit:", prb_fit)

        # Plot results
        if plot:
            try:
                plot_rb_single(rb_fit, title=f"{rb_type} RB Decay", x_axis_mode=self.x_axis_mode)
                plot_prb_single(prb_fit, num_qubits=self.num_qubits, title=f"{rb_type} PRB Decay")
            except Exception as e:
                logging.warning(f"[WARN] Plot failed: {e}")

        rb_fit["fit_successful"] = rb_fit.get("fit_successful", False)
        return {
            "rb_fit": rb_fit,
            "prb_fit": prb_fit,
            "fit_successful": rb_fit.get("fit_successful", False),
        }


# =============================================================================
# Interleaved Randomized Benchmarking Experiment
# =============================================================================
class InterleavedRBExperiment(StandardRBExperiment):
    """Interleaved RB with per-gate EPG and fidelity."""

    _CLIFFORD_NAMES = {
        "i",
        "id",
        "x",
        "y",
        "z",
        "h",
        "s",
        "sdg",
        "sx",
        "sxdg",
        "sy",
        "sydg",
        "rx90",
        "ry90",
        "cx",
        "cnot",
        "cz",
        "swap",
        "ccnot",
        "fredkin",
        "cswap",
        "ccz",
        "ecr",
    }

    def __init__(
        self,
        qubits: Union[int, List[int]],
        interleaved_gate: Gate,
        depths: Optional[List[int]] = None,
        circuits_per_depth: int = DEFAULT_CIRCUITS_PER_DEPTH,
        native_gates: Optional[List[str]] = None,
        seed: Optional[Union[int, float]] = None,
        clifford_factory: Optional[Union[CliffordFactory, str]] = None,
        x_axis_mode: str = "GATE_COUNT",
    ):
        if clifford_factory is None:
            cf = CliffordGateSet()
            cf.two_qubit_gate_name = "cz"
            clifford_factory = cf
            logging.info("[IRB] Using default CZ-based Clifford factory.")
        elif isinstance(clifford_factory, str):
            cf = get_gate_set(clifford_factory)
            if isinstance(cf, CliffordGateSet) and getattr(
                cf, "two_qubit_gate_name", ""
            ).lower() == "cnot":
                cf.two_qubit_gate_name = "cz"
                logging.info("[IRB] Factory switched to CZ-based randomization.")
            clifford_factory = cf

        super().__init__(
            qubits=qubits,
            depths=depths,
            circuits_per_depth=circuits_per_depth,
            native_gates=native_gates,
            seed=seed,
            clifford_factory=clifford_factory,
            x_axis_mode=x_axis_mode,
        )

        self.interleaved_gate = interleaved_gate
        self.num_qubits = len(self.qubits)
        self._is_clifford_gate = (
            self.num_qubits == 1 or interleaved_gate.name.lower() in self._CLIFFORD_NAMES
        )
        if self._is_clifford_gate:
            logging.info(f"[IRB] Target gate '{interleaved_gate.name}' is Clifford.")
        else:
            logging.warning(
                f"[IRB] Gate '{interleaved_gate.name}' NOT Clifford - non-inverting."
            )

    def _generate_single_interleaved_circuit(
        self, depth: int, seed: Optional[Union[int, float]] = None
    ) -> QuantumCircuit:
        rng = random.Random(seed)
        circ = QuantumCircuit(qubits=self.qubits)
        if depth == 0:
            circ.measure_all()
            circ.metadata.update({"depth": 0, "gate_count": 0, "seed": seed})
            return circ

        forward_seq: List[Gate] = []
        for _ in range(depth):
            fwd, _ = self.clifford_factory.get_random_clifford_and_inverse(
                self.qubits, rng.random()
            )
            forward_seq.extend(fwd)
            forward_seq.append(self.interleaved_gate)

        for g in forward_seq:
            circ.add_gate(g)

        if self._is_clifford_gate:
            inv_circ = QuantumCircuit(self.qubits)
            inv_circ.add_gates(forward_seq)
            circ.add_gates(inv_circ.inverse().gates)

        circ.measure_all()
        circ.metadata.update(
            {
                "depth": depth,
                "gate_count": len(circ.gates),
                "seed": seed,
                "mode": "interleaved",
                "interleaved_gate": self.interleaved_gate.name,
            }
        )
        if self.native_gates:
            circ = circ.decompose(basis_gates=self.native_gates)
        return circ

    def circuits(self) -> List[QuantumCircuit]:
        rng = random.Random(self.seed)
        return [
            self._generate_single_interleaved_circuit(d, rng.random())
            for d in self.depths
            for _ in range(self.circuits_per_depth)
        ]

    def run(
        self,
        circuits_ref: Optional[List[QuantumCircuit]] = None,
        circuits_int: Optional[List[QuantumCircuit]] = None,
        engine: Optional[QuantumEngine] = None,
        shots: int = 2048,
        plot: bool = True,
        experimental_data_by_depth_ref: Optional[Dict[int, List[Dict[str, float]]]] = None,
        experimental_data_by_depth_int: Optional[Dict[int, List[Dict[str, float]]]] = None,
        experimental_results_ref: Optional[List[Dict[str, float]]] = None,
        experimental_results_int: Optional[List[Dict[str, float]]] = None,
        debug: bool = False,
    ) -> Dict[str, Any]:
        gname = self.interleaved_gate.name.upper()
        logging.info(f"=== Interleaved RB for gate '{gname}' ===")

        # Generate circuits automatically if needed
        if engine and (circuits_ref is None or circuits_int is None):
            ref_exp = StandardRBExperiment(
                self.qubits,
                self.depths,
                self.circuits_per_depth,
                self.native_gates,
                self.seed,
                self.clifford_factory,
                self.x_axis_mode,
            )
            circuits_ref = ref_exp.circuits()
            circuits_int = self.circuits()
            logging.info("[IRB] Auto-generated reference and interleaved circuits.")

        ref_exp = StandardRBExperiment(
            self.qubits,
            self.depths,
            self.circuits_per_depth,
            self.native_gates,
            self.seed,
            self.clifford_factory,
            self.x_axis_mode,
        )
        ref_res = ref_exp.run(
            circuits_ref,
            engine,
            shots,
            plot=False,
            experimental_results=experimental_results_ref,
            experimental_data_by_depth=experimental_data_by_depth_ref,
            debug=debug,
        )

        int_res = StandardRBExperiment.run(
            self,
            circuits_int,
            engine,
            shots,
            plot=False,
            experimental_results=experimental_results_int,
            experimental_data_by_depth=experimental_data_by_depth_int,
            debug=debug,
        )

        epg = calculate_epg(ref_res["rb_fit"]["p"], int_res["rb_fit"]["p"], self.num_qubits)
        fidelity = 1.0 - epg
        gate_err_prb = calculate_prb_gate_error(
            ref_res["prb_fit"], int_res["prb_fit"], self.num_qubits
        )

        print("\n================= Interleaved RB Result =================")
        print(f"Target gate           : {gname.lower()}")
        print(f"Estimated fidelity     : {fidelity:.6f}")
        print(f"Estimated gate error   : {epg:.6e}")
        if gate_err_prb["calculation_successful"]:
            print(f"PRB gate error         : {gate_err_prb['gate_error']:.6e}")
        print("==========================================================\n")

        if plot:
            try:
                plot_rb_comparison(
                    ref_res["rb_fit"],
                    int_res["rb_fit"],
                    target_gate_name=gname,
                    x_axis_mode=self.x_axis_mode,
                )
                plot_prb_comparison(
                    ref_res["prb_fit"],
                    int_res["prb_fit"],
                    target_gate_name=gname,
                )
            except Exception as e:
                logging.warning(f"[WARN] Plot comparison failed: {e}")

        return {
            "epg": epg,
            "fidelity": fidelity,
            "prb_gate_error": gate_err_prb,
            "rb_fit_ref": ref_res["rb_fit"],
            "rb_fit_int": int_res["rb_fit"],
            "prb_fit_ref": ref_res["prb_fit"],
            "prb_fit_int": int_res["prb_fit"],
            "is_clifford_gate": self._is_clifford_gate,
        }

# =============================================================================
# End of File
# =============================================================================