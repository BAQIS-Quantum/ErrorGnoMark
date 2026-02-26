# =============================================================================
# File: csb_cz.py
# Purpose: CZ Enhanced CSB analysis (phase + infidelities)
# =============================================================================

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


def _expectation_from_counts(counts: Dict[str, int]) -> float:
    """Compute ⟨ZZ⟩-parity expectation from two-qubit counts."""
    shots = sum(counts.values())
    if shots == 0:
        return 0.0

    p00 = counts.get("00", 0) / shots
    p01 = counts.get("01", 0) / shots
    p10 = counts.get("10", 0) / shots
    p11 = counts.get("11", 0) / shots

    return p00 + p11 - p01 - p10


def _average_expectation(counts: List[Dict[str, int]]) -> float:
    """Average expectation value over repeated circuits."""
    return float(np.mean([_expectation_from_counts(c) for c in counts]))


def build_cz_enhanced_csb_signal(
    results: Dict[int, Dict[str, List[Dict[str, int]]]]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Construct the Enhanced CSB complex signal:

        S(L) = ⟨XX⟩ + i⟨YY⟩

    indexed by circuit depth L.
    """
    depths = sorted(results.keys())
    signal = []

    for depth in depths:
        entry = results[depth]
        ox = _average_expectation(entry["ox"])
        oy = _average_expectation(entry["oy"])
        signal.append(ox + 1j * oy)

    return np.asarray(depths, dtype=int), np.asarray(signal, dtype=complex)


def _estimate_phi_and_decay(signal: np.ndarray) -> Tuple[float, float]:
    """
    Estimate the CZ phase and dominant spectral decay from the CSB signal.
    """
    if signal.size < 2:
        raise ValueError("CZ Enhanced CSB requires at least two depths")

    phase_steps = np.angle(signal[1:] * np.conj(signal[:-1]))
    phi = float(np.angle(np.mean(np.exp(1j * phase_steps))))

    decay = float(np.mean(np.abs(signal[1:]) / np.abs(signal[:-1])))

    return phi, decay


def _estimate_infidelities_from_decay(decay: float) -> Tuple[float, float]:
    """
    Map CSB decay to infidelities under an isotropic PTM noise assumption.

    Returns:
        stochastic_infidelity
        process_infidelity
    """
    stochastic_infidelity = 1.0 - np.sqrt(decay)

    d = 4  # two-qubit CZ
    f_avg = (d * decay + 1.0) / (d + 1.0)
    process_infidelity = 1.0 - f_avg

    return float(stochastic_infidelity), float(process_infidelity)


def analyze_cz_enhanced_csb(
    cz_csb_results: Dict[int, Dict[str, List[Dict[str, int]]]]
) -> Dict[str, float]:
    """
    Perform final CZ Enhanced CSB analysis.

    Returns:
        {
            "phi": extracted CZ phase,
            "stochastic_infidelity": ...,
            "process_infidelity": ...
        }
    """
    _, signal = build_cz_enhanced_csb_signal(cz_csb_results)

    phi, decay = _estimate_phi_and_decay(signal)
    r_stoch, r_proc = _estimate_infidelities_from_decay(decay)

    return {
        "phi": phi,
        "stochastic_infidelity": r_stoch,
        "process_infidelity": r_proc,
    }

    # -----------------------------------------------------------------------------
# Data processing methodology
# -----------------------------------------------------------------------------
#
# This module performs a post-processing analysis of CZ Enhanced CSB data
# following a split-estimation strategy:
#
# (1) Raw data handling
#     Input data are grouped by circuit depth L. For each depth, measurement
#     results are provided as lists of two-qubit bitstring count dictionaries
#     for Ox- and Oy-type circuits. No shot-level rescaling or filtering is
#     applied at this stage.
#
# (2) Expectation value estimation
#     For each circuit instance, a parity expectation value is computed from
#     the raw counts. Expectation values are then averaged over all random
#     circuits at the same depth to suppress sampling noise.
#
# (3) Enhanced CSB signal construction
#     The averaged expectations are combined into a complex signal
#
#         S(L) = <XX> + i<YY>
#
#     which isolates the coherent CZ phase as the dominant spectral component.
#
# (4) Phase and decay estimation
#     The CZ phase is extracted from the mean phase advance between consecutive
#     depths using a circular mean estimator. The signal magnitude decay is
#     estimated from the ratio |S(L+1)| / |S(L)| and interpreted as a dominant
#     spectral decay factor.
#
# (5) Infidelity inference
#     Under the assumption of approximately isotropic and gate-independent
#     noise in the Pauli transfer matrix representation, the extracted decay
#     factor is mapped analytically to stochastic and process infidelities.
#
# This analysis intentionally targets only the dominant spectral component.
# Full spectral reconstruction and model-specific noise characterization are
# outside the scope of this module.
#