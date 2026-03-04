# =============================================================================
# File    : egm/core/experiments/benchmarking/csb_cphase.py
# Version : v1.2 – Standard CPhase CSB Reference Experiment (Frozen)
# =============================================================================
"""
Standard CPhase (CZ) Channel Spectrum Benchmarking Experiment

Design principles (FROZEN):
---------------------------
• Semantic‑level Experiment (Reference Runner)
• Minimal end‑to‑end CSB execution path
• Assumes an internal backend interface: backend.execute(circuits)
• No RB‑style execution mode generalization
• Circuit generation via module‑level pure functions
• All CSB mathematics delegated to analyzer
• run() assembles the pipeline only
• run() returns analyzer result verbatim

Physical scope:
---------------
• Only supports CPhase / CZ‑like gates: diag(1, 1, 1, e^{iφ})
• No fsim / iSWAP / general CSB
"""

from __future__ import annotations

import logging
import random
from typing import List, Dict, Optional, Union

from egm.core.circuits.circuit import QuantumCircuit, Gate
from egm.core.execution.executor import QuantumEngine

# Pure CSB analysis (no backend / circuit dependency)
from egm.core.analysis.csb_cphase import analyze_csb_cphase

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# =============================================================================
# Module‑level Circuit Generation (PURE FUNCTIONS)
# =============================================================================

def generate_single_cphase_csb_circuit(
    *,
    qubits: List[int],
    depth: int,
    rep: int,
    target_phase: float,
    seed: Optional[Union[int, float]],
    csb_index: int,
) -> QuantumCircuit:
    """
    Generate a single CPhase CSB circuit.

    Pure function:
        • no backend
        • no analyzer
        • no experiment state

    Notes:
        • `csb_index` defines the spectral time axis (legacy CSB requirement)
        • `depth` is a physical circuit parameter, NOT the spectral index
    """
    rng = random.Random(seed)
    circ = QuantumCircuit(qubits=qubits)

    # Minimal CZ‑CSB pattern (extendable, analyzable)
    for _ in range(depth):
        for _ in range(rep):
            circ.add_gate(Gate("cz", (qubits[0], qubits[1])))

    circ.measure_all()
    circ.metadata.update(
        {
            "experiment_type": "CSB-CPhase",
            "gate": "CZ",

            # CSB semantics
            "csb_index": csb_index,   # ✅ spectral index (0,1,2,...)
            "depth": depth,           # physical circuit depth
            "rep": rep,
            "target_phase": target_phase,

            # bookkeeping
            "seed": seed,
        }
    )
    return circ


def generate_cphase_csb_circuits(
    *,
    qubits: List[int],
    depths: List[int],
    circuits_per_depth: int,
    rep: int,
    target_phase: float,
    seed: Optional[Union[int, float]],
) -> List[QuantumCircuit]:
    """
    Generate the full set of CPhase CSB circuits.

    IMPORTANT:
        • `depths` may be non‑uniform (e.g. [1,2,4,8,...])
        • CSB spectral ordering is defined by `csb_index = enumerate(depths)`
    """
    circuits: List[QuantumCircuit] = []
    rng = random.Random(seed)

    for csb_index, depth in enumerate(depths):
        for _ in range(circuits_per_depth):
            circuits.append(
                generate_single_cphase_csb_circuit(
                    qubits=qubits,
                    depth=depth,
                    rep=rep,
                    target_phase=target_phase,
                    seed=rng.random(),
                    csb_index=csb_index,
                )
            )

    return circuits


# =============================================================================
# Standard CPhase CSB Experiment (REFERENCE RUNNER)
# =============================================================================

class StandardCPhaseCSBExperiment:
    """
    Standard CPhase / CZ CSB Experiment.

    Internal structure (FROZEN):
        1. Circuit acquisition
        2. Backend execution & data collection
        3. Inline centralized analysis
        4. run() assembles the pipeline only
    """

    # -----------------------------------------------------------------
    # Initialization
    # -----------------------------------------------------------------
    def __init__(
        self,
        *,
        qubits: Union[int, List[int]],
        depths: List[int],
        circuits_per_depth: int,
        target_phase: float,
        rep: int = 1,
        seed: Optional[Union[int, float]] = None,
    ):
        self.qubits = [qubits] if isinstance(qubits, int) else qubits
        self.num_qubits = len(self.qubits)

        self.depths = depths
        self.circuits_per_depth = circuits_per_depth

        self.target_phase = target_phase
        self.rep = rep
        self.seed = seed

        logging.info(
            f"[CSB-Init] Standard CPhase CSB initialized "
            f"({self.num_qubits}Q, target_phase={self.target_phase})"
        )

    # -----------------------------------------------------------------
    # 1. Circuit acquisition
    # -----------------------------------------------------------------
    def circuits(self) -> List[QuantumCircuit]:
        """
        Acquire CSB circuits via pure generator functions.
        """
        return generate_cphase_csb_circuits(
            qubits=self.qubits,
            depths=self.depths,
            circuits_per_depth=self.circuits_per_depth,
            rep=self.rep,
            target_phase=self.target_phase,
            seed=self.seed,
        )

    # -----------------------------------------------------------------
    # 2. Backend execution & data acquisition
    # -----------------------------------------------------------------
    def _execute(
        self,
        engine: QuantumEngine,
        circuits: List[QuantumCircuit],
    ) -> Dict[int, List[Dict[str, int]]]:
        """
        Execute circuits and collect raw bitstring counts,
        organized by CSB spectral index.

        Returns:
            Dict[csb_index, List[counts]]
        """
        logging.info(
            f"[CSB-Execute] Submitting {len(circuits)} circuits to backend."
        )

        results = engine.execute_with_ideal(
            circuits,
            shots=engine.backend.shots if hasattr(engine.backend, "shots") else 1024,
        )

        counts_by_index: Dict[int, List[Dict[str, int]]] = {
            i: [] for i in range(len(self.depths))
        }

        for circ, (_, noisy_counts) in zip(circuits, results):
            csb_index = circ.metadata["csb_index"]
            counts_by_index[csb_index].append(noisy_counts)

        return counts_by_index

    # -----------------------------------------------------------------
    # 3–4. Reference Runner (FINAL)
    # -----------------------------------------------------------------
    def run(
        self,
        backend: QuantumEngine,
        *,
        cutoff: float = 1e-10,
    ):
        """
        Run the complete CSB reference pipeline.

        Execution flow (FROZEN):
            circuits → execute → analyze

        Returns:
            CSBAnalysisResult (verbatim from analyzer)
        """
        circuits = self.circuits()
        experiment_results = self._execute(backend, circuits)

        return analyze_csb_cphase(
            experiment_results,
            target_phase=self.target_phase,
            rep=self.rep,
            cutoff=cutoff,
        )

# =============================================================================
# End of File
# =============================================================================