# =============================================================================
# File    : egm/core/experiments/benchmarking/csb_cz_enhanced.py
# Version : v2.1 – CZ Enhanced CSB (Split-Estimation)
# =============================================================================
"""
CZ Enhanced Channel Spectrum Benchmarking experiment.

This implementation provides a complete CZ Enhanced CSB workflow with
explicit separation of responsibilities:

Capabilities:
  - Estimate CZ phase via dominant-spectral CSB (model-independent)
  - Estimate an effective decay rate
  - Infer stochastic and process infidelity from decay under an
    explicitly stated noise assumption

Limitations:
  - No full PTM spectral tomography
  - Infidelity estimates are not fully model-free
"""

from __future__ import annotations

import logging
import random
import uuid
from typing import Dict, List, Optional, Union

import numpy as np

from egm.core.circuits.circuit import QuantumCircuit, Gate
from egm.core.engine.executor import QuantumEngine
from egm.schemas.results.csb import CSBAnalysisResult, AnalysisStatus

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# =============================================================================
# 1. Circuit generation
# =============================================================================

def generate_single_cz_enhanced_csb_circuit(
    *,
    qubits: List[int],
    depth: int,
    rep: int,
    observable: str,
    seed: float,
    csb_index: int,
    target_phase: Optional[float],
) -> QuantumCircuit:
    """
    Generate a single CZ Enhanced CSB circuit.

    The seed and target_phase parameters are recorded in metadata
    for traceability only and do not affect circuit construction.
    """
    if observable not in ("ox", "oy"):
        raise ValueError("observable must be 'ox' or 'oy'")

    q0, q1 = qubits
    circ = QuantumCircuit(qubits=qubits)

    circ.add_gate(Gate("h", (q0,)))
    circ.add_gate(Gate("h", (q1,)))
    circ.add_gate(Gate("x", (q0,)))  # parity breaking

    for _ in range(depth):
        for _ in range(rep):
            circ.add_gate(Gate("cz", (q0, q1)))

    if observable == "ox":
        circ.add_gate(Gate("h", (q0,)))
        circ.add_gate(Gate("h", (q1,)))
    else:
        circ.add_gate(Gate("sdg", (q0,)))
        circ.add_gate(Gate("h", (q0,)))
        circ.add_gate(Gate("sdg", (q1,)))
        circ.add_gate(Gate("h", (q1,)))

    circ.measure_all()

    circ.metadata.update(
        {
            "experiment_type": "CSB-CZ-Enhanced",
            "gate": "CZ",
            "observable": observable,
            "csb_index": csb_index,
            "depth": depth,
            "rep": rep,
            "seed": seed,
            "target_phase": target_phase,
        }
    )

    return circ


def generate_cz_enhanced_csb_circuits(
    *,
    qubits: List[int],
    depths: List[int],
    circuits_per_depth: int,
    rep: int,
    seed: Optional[Union[int, float]],
    target_phase: Optional[float],
) -> List[QuantumCircuit]:
    rng = random.Random(seed)
    circuits: List[QuantumCircuit] = []

    for csb_index, depth in enumerate(depths):
        for _ in range(circuits_per_depth):
            for obs in ("ox", "oy"):
                circuits.append(
                    generate_single_cz_enhanced_csb_circuit(
                        qubits=qubits,
                        depth=depth,
                        rep=rep,
                        observable=obs,
                        seed=rng.random(),
                        csb_index=csb_index,
                        target_phase=target_phase,
                    )
                )
    return circuits


# =============================================================================
# 2. Phase estimator (dominant-spectral CSB)
# =============================================================================

class CZCSBPhaseEstimator:
    """
    Dominant-spectral CZ Enhanced CSB phase estimator.

    Outputs:
      - phase (single-CZ phase)
      - phase_error (diagnostic, optional)
      - decay (effective dominant spectral decay)
    """

    @staticmethod
    def _expectation_from_counts(counts: Dict[str, int]) -> float:
        shots = sum(counts.values())
        if shots == 0:
            return 0.0

        p00 = counts.get("00", 0) / shots
        p01 = counts.get("01", 0) / shots
        p10 = counts.get("10", 0) / shots
        p11 = counts.get("11", 0) / shots
        return p00 + p11 - p01 - p10

    def estimate(
        self,
        results: Dict[int, Dict[str, List[Dict[str, int]]]],
        *,
        rep: int,
        target_phase: Optional[float],
    ) -> Dict[str, Optional[float]]:

        depths = sorted(results.keys())
        signal = []

        for d in depths:
            ox = np.mean(
                [self._expectation_from_counts(c) for c in results[d]["ox"]]
            )
            oy = np.mean(
                [self._expectation_from_counts(c) for c in results[d]["oy"]]
            )
            signal.append(ox + 1j * oy)

        signal = np.asarray(signal, complex)

        phase_steps = np.angle(signal[1:] * np.conj(signal[:-1]))
        phase = float(np.angle(np.mean(np.exp(1j * phase_steps))))
        phase /= rep

        decay = float(np.mean(np.abs(signal[1:]) / np.abs(signal[:-1])))

        if target_phase is None:
            phase_error = None
        else:
            phase_error = float(
                abs((phase - target_phase + np.pi) % (2 * np.pi) - np.pi)
            )

        return {
            "phase": phase,
            "phase_error": phase_error,
            "decay": decay,
        }


# =============================================================================
# 3. Infidelity estimator (assumption-based)
# =============================================================================

class CZInfidelityEstimator:
    """
    Estimate stochastic and process infidelity from decay.

    Assumes isotropic noise in the non-identity PTM subspace (d = 4).
    """

    def estimate(self, decay: float) -> Dict[str, float]:
        d = 4
        dim2 = d * d

        process_infidelity = 1.0 - (1.0 + (dim2 - 1) * decay) / dim2
        stochastic_infidelity = (
            1.0
            - np.sqrt((1.0 + (dim2 - 1) * decay**2) / dim2)
        )

        return {
            "stochastic_infidelity": float(stochastic_infidelity),
            "process_infidelity": float(process_infidelity),
            "infidelity_model": "isotropic-PTM (assumption-based)",
        }


# =============================================================================
# 4. Experiment orchestration
# =============================================================================

class CZEnhancedCSBExperiment:
    """
    Complete CZ Enhanced CSB experiment using split estimation.
    """

    def __init__(
        self,
        *,
        qubits: Union[int, List[int]],
        depths: List[int],
        circuits_per_depth: int,
        rep: int = 1,
        seed: Optional[Union[int, float]] = None,
        target_phase: Optional[float] = None,
    ):
        self.qubits = [qubits] if isinstance(qubits, int) else qubits
        if len(self.qubits) != 2:
            raise ValueError("CZ Enhanced CSB requires exactly two qubits")

        self.depths = depths
        self.circuits_per_depth = circuits_per_depth
        self.rep = rep
        self.seed = seed
        self.target_phase = target_phase

        self.phase_estimator = CZCSBPhaseEstimator()
        self.infidelity_estimator = CZInfidelityEstimator()

    def _execute(
        self,
        engine: QuantumEngine,
        circuits: List[QuantumCircuit],
    ) -> Dict[int, Dict[str, List[Dict[str, int]]]]:

        results = engine.execute_with_ideal(
            circuits,
            shots=getattr(engine.backend, "shots", 1024),
        )

        counts_by_index = {
            i: {"ox": [], "oy": []} for i in range(len(self.depths))
        }

        for circ, (_, counts) in zip(circuits, results):
            idx = circ.metadata["csb_index"]
            obs = circ.metadata["observable"]
            counts_by_index[idx][obs].append(counts)

        return counts_by_index

    def run(self, backend: QuantumEngine) -> CSBAnalysisResult:
        if self.target_phase is None:
            raise ValueError("target_phase must be specified")

        circuits = generate_cz_enhanced_csb_circuits(
            qubits=self.qubits,
            depths=self.depths,
            circuits_per_depth=self.circuits_per_depth,
            rep=self.rep,
            seed=self.seed,
            target_phase=self.target_phase,
        )

        experiment_results = self._execute(backend, circuits)

        phase_metrics = self.phase_estimator.estimate(
            experiment_results,
            rep=self.rep,
            target_phase=self.target_phase,
        )

        inf_metrics = self.infidelity_estimator.estimate(
            phase_metrics["decay"]
        )

        return CSBAnalysisResult(
            plan_id=uuid.uuid4(),
            qubits=self.qubits,
            analyzer_version="cz-enhanced-csb-split-v2.1",
            raw_data_ids=[],
            status=AnalysisStatus.SUCCESS,
            message=(
                "CZ Enhanced CSB completed. "
                "Phase estimated via dominant-spectral CSB; "
                "infidelity inferred from decay under isotropic-noise assumption."
            ),
            phase=phase_metrics["phase"],
            phase_error=phase_metrics["phase_error"],
            stochastic_infidelity=inf_metrics["stochastic_infidelity"],
            process_infidelity=inf_metrics["process_infidelity"],
            metadata={
                "depths": self.depths,
                "circuits_per_depth": self.circuits_per_depth,
                "rep": self.rep,
                "target_phase": self.target_phase,
                "analysis_mode": "split-estimation",
                "infidelity_model": inf_metrics["infidelity_model"],
            },
        )


# -----------------------------------------------------------------------------
# Data processing methodology
# -----------------------------------------------------------------------------
#
# 1. Circuit grouping
#    Circuits are grouped by depth index. For each depth, Ox and Oy
#    circuits are executed independently and aggregated.
#
# 2. Signal construction
#    For each depth L, averaged parity expectations are combined into
#
#        S(L) = <XX> + i<YY>
#
#    forming the Enhanced CSB complex signal.
#
# 3. Phase estimation
#    The CZ phase is extracted from the average phase advance between
#    successive depths using a dominant-spectral estimator. The result
#    is normalized by the repetition factor rep to obtain the single-CZ
#    phase.
#
# 4. Decay and infidelity inference
#    The magnitude decay of the signal is interpreted as a dominant
#    spectral decay factor. Under an isotropic PTM noise assumption,
#    this decay is mapped analytically to stochastic and process
#    infidelities.
#
# 5. Scope
#    This experiment targets only the dominant spectral component.
#    Full spectral reconstruction and fully model-free infidelity
#    estimation are outside the scope of this implementation.
#
# =============================================================================
# End of file
# =============================================================================