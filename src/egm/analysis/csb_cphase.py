# =============================================================================
# File: egm/core/analysis/csb_cphase.py
# =============================================================================

from __future__ import annotations

import logging
import numpy as np
from typing import Dict, List
from uuid import uuid4

from egm.schemas.results.csb import (
    CSBAnalysisResult,
    CSBSequenceDataPoint,
    AnalysisStatus,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# ------------------------------------------------------------------
# Two‑point single‑pole phase estimator (CSB‑correct for demo)
# ------------------------------------------------------------------
def _estimate_phase_two_point(signal: np.ndarray) -> float:
    """
    Estimate phase using adjacent CSB evolution points:
        φ ≈ arg( signal[k+1] / signal[k] )
    """
    for k in range(len(signal) - 1):
        if abs(signal[k]) > 1e-6:
            return np.angle(signal[k + 1] / signal[k])

    raise ValueError("Insufficient non‑zero CSB signal")


# ------------------------------------------------------------------
# CSB‑CZ core analysis (minimal, correct for current experiment)
# ------------------------------------------------------------------
def compute_csb_q2cz(
    bitstring_counts: List[Dict[str, int]],
    *,
    target_phase: float,
):
    # ------------------------------------------------------------
    # Build parity observable ⟨Z⊗Z⟩
    # ------------------------------------------------------------
    signal = []
    for counts in bitstring_counts:
        shots = sum(counts.values())
        if shots == 0:
            continue

        p00 = counts.get("00", 0) / shots
        p01 = counts.get("01", 0) / shots
        p10 = counts.get("10", 0) / shots
        p11 = counts.get("11", 0) / shots

        signal.append(p00 + p11 - p01 - p10)

    signal = np.asarray(signal, dtype=float)

    if len(signal) < 2:
        raise ValueError("At least 2 CSB points required")

    # ------------------------------------------------------------
    # Remove DC
    # ------------------------------------------------------------
    signal = signal - np.mean(signal)

    # ------------------------------------------------------------
    # Phase extraction (two‑point)
    # ------------------------------------------------------------
    dominant_phase = _estimate_phase_two_point(signal)

    phase_error = (dominant_phase - target_phase + np.pi) % (2 * np.pi) - np.pi

    return {
        "dominant_phase": float(dominant_phase),
        "phase_error": float(abs(phase_error)),
    }


# ------------------------------------------------------------------
# Public CSB‑CPhase analysis API
# ------------------------------------------------------------------
def analyze_csb_cphase(
    experiment_results: Dict[int, List[Dict[str, int]]],
    *,
    target_phase: float,
    rep: int = 1,
    cutoff: float = 1e-10,
):
    csb_indices = sorted(experiment_results.keys())

    # --------------------------------------------------
    # Display data (unchanged)
    # --------------------------------------------------
    sequence_data: List[CSBSequenceDataPoint] = []
    for idx in csb_indices:
        for counts in experiment_results[idx]:
            shots = sum(counts.values())
            p11 = counts.get("11", 0) / shots if shots > 0 else 0.0
            sequence_data.append(
                CSBSequenceDataPoint(
                    sequence_length=idx,
                    probability=float(p11),
                    std_error=None,
                )
            )

    # --------------------------------------------------
    # True CSB evolution points (even indices)
    # --------------------------------------------------
    evolution_counts: List[Dict[str, int]] = []
    for idx in csb_indices:
        if idx % 2 != 0:
            continue

        total: Dict[str, int] = {}
        for counts in experiment_results[idx]:
            for k, v in counts.items():
                total[k] = total.get(k, 0) + v

        evolution_counts.append(total)

    try:
        metrics = compute_csb_q2cz(
            evolution_counts,
            target_phase=target_phase,
        )

        return CSBAnalysisResult(
            plan_id=uuid4(),
            qubits=[0, 1],
            analyzer_version="csb-cphase-two-point",
            raw_data_ids=[],
            status=AnalysisStatus.SUCCESS,
            message="CSB CZ phase φ extracted (two‑point).",
            sequence_data=sequence_data,
            dominant_phase=metrics["dominant_phase"],
            phase_error=metrics["phase_error"],
            process_infidelity=None,
            stochastic_infidelity=None,
        )

    except Exception as exc:
        logging.exception("CSB‑CPhase analysis failed")
        return CSBAnalysisResult(
            plan_id=uuid4(),
            qubits=[0, 1],
            analyzer_version="csb-cphase-two-point",
            raw_data_ids=[],
            status=AnalysisStatus.FAILED,
            message=str(exc),
            sequence_data=sequence_data,
        )

# =============================================================================
# End of File
# =============================================================================