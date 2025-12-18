# File: egm/core/analysis/xeb.py
# [v3.0 Re‑Architected – RB‑Style Modular Layout]
# -------------------------------------------------------------------
# Cross‑Entropy Benchmarking (XEB) & Speckle Purity Benchmarking (SPB)
# -------------------------------------------------------------------
# Responsibilities:
#   • Compute XEB linear fidelity per circuit
#   • Fit fidelity decay to exponential model F(d) = A · p^d + B
#   • Integrate SPB purity analysis & combined decay fitting
#   • Expose structured results for experiment orchestration
#
# Visualization:
#   All plotting functions are delegated to
#   egm.reporting.visualizers.xeb_plotter
# -------------------------------------------------------------------

import logging
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import sem
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

from egm.core.analysis.spb import analyze_speckle_purity, fit_spb_decay

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


# ===================================================================
#  SECTION 1.  XEB FIDELITY CALCULATION
# ===================================================================

def analyze_xeb_fidelity(
    ideal_probabilities: Dict[str, float],
    noisy_counts: Dict[str, float],
    num_qubits: int
) -> float:
    """
    Compute the normalized linear XEB fidelity for a single circuit.

    Args:
        ideal_probabilities (Dict[str, float]):
            The theoretical outcome probabilities for each bitstring.
        noisy_counts (Dict[str, float]):
            Measured experimental data; can be raw counts or normalized probabilities.
        num_qubits (int):
            Number of qubits in the circuit.

    Returns:
        float: The normalized XEB fidelity value for this circuit.
    """
    total = sum(noisy_counts.values())
    if total == 0:
        return 0.0

    xeb_sum = 0.0
    for bitstring, count in noisy_counts.items():
        p_meas = count / total
        p_ideal = ideal_probabilities.get(bitstring, 0.0)
        xeb_sum += p_ideal * p_meas

    d = 2 ** num_qubits
    raw = d * xeb_sum - 1.0
    fidelity = ((d + 1) / (d - 1)) * raw
    return max(0.0, min(fidelity, 1.0))


# ===================================================================
#  SECTION 2.  FITTING OF FIDELITY DECAY
# ===================================================================

def _exp_decay(x: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """Exponential decay model: F(x) = A * p^x + B."""
    return A * np.power(p, x) + B


def fit_xeb_decay(
    x_values: List[int],
    fidelities_by_x: Dict[int, List[float]],
    num_qubits: int
) -> Dict[str, Any]:
    """
    Fit the averaged XEB fidelity data to an exponential decay model.

    Returns:
        dict: {'A', 'p', 'B', 'epc'} where 'epc' is the error per cycle.
    """
    avg_fidelities = np.array([np.mean(fidelities_by_x[x]) for x in x_values])
    initial = [1.0, 0.999, 0.0]
    bounds = ([0.0, 0.0, -0.1], [1.5, 1.0, 0.3])

    try:
        params, _ = curve_fit(
            _exp_decay,
            np.asarray(x_values, dtype=float),
            avg_fidelities,
            p0=initial,
            bounds=bounds
        )
    except RuntimeError:
        logger.warning("XEB exponential decay fit failed; using default parameters.")
        params = initial

    A, p, B = params
    epc = 1.0 - p
    return {'A': A, 'p': p, 'B': B, 'epc': epc}


# ===================================================================
#  SECTION 3.  XEB + SPB ORCHESTRATION
# ===================================================================

def analyze_xeb_and_spb_from_results(
    results_by_x: Dict[int, List[Tuple[Dict, Dict]]],
    num_qubits: int
) -> Dict[str, Any]:
    """
    Perform unified analysis combining XEB and SPB on the same dataset.

    The function adaptively handles both count-based and probability-based
    inputs, ensuring numerical stability across different user data formats.

    Args:
        results_by_x (Dict[int, List[Tuple[Dict, Dict]]]):
            Dictionary mapping circuit depth (or noise exponent)
            to a list of tuples containing:
              (ideal_probabilities, measured_counts_or_probabilities)
        num_qubits (int):
            Number of qubits in the circuit.

    Returns:
        dict: Combined results structured as:
            {
              "xeb_analysis": {"raw_data": ..., "fit_results": ...},
              "spb_analysis": {"raw_data": ..., "fit_results": ...}
            }
    """

    fidelities_by_x = defaultdict(list)
    purities_by_x = defaultdict(list)
    x_values = sorted(results_by_x.keys())

    for depth in x_values:
        samples = results_by_x[depth]
        for ideal_probs, noisy in samples:
            # Compute XEB fidelity — valid for both counts or probabilities
            fidelities_by_x[depth].append(
                analyze_xeb_fidelity(ideal_probs, noisy, num_qubits)
            )

            # --- Smart detection: determine whether `noisy` is counts or probabilities ---
            if not noisy:
                purities_by_x[depth].append(np.nan)
                continue

            values = np.array(list(noisy.values()))
            is_prob_dist = (
                np.all((values >= 0) & (values <= 1))
                and abs(np.sum(values) - 1.0) < 1e-3
            )

            if is_prob_dist:
                # Convert probabilities to pseudo-counts
                N = 4096  # Default pseudo number of shots (can be adjusted or linked to experiment shots)
                pseudo_counts = {k: int(round(v * N)) for k, v in noisy.items()}
                if sum(pseudo_counts.values()) < 2:
                    # Ensure nonzero denominator in unbiased purity estimator
                    pseudo_counts = {k: max(1, int(round(v * N))) for k, v in noisy.items()}
                noisy_for_spb = pseudo_counts
            else:
                noisy_for_spb = {k: int(v) for k, v in noisy.items()}

            purity_val = analyze_speckle_purity(ideal_probs, noisy_for_spb, num_qubits)
            purities_by_x[depth].append(purity_val)

    xeb_fit_results = fit_xeb_decay(x_values, fidelities_by_x, num_qubits)
    spb_fit_results = fit_spb_decay(x_values, purities_by_x)

    return {
        "xeb_analysis": {"raw_data": fidelities_by_x, "fit_results": xeb_fit_results},
        "spb_analysis": {"raw_data": purities_by_x, "fit_results": spb_fit_results},
    }


# ===================================================================
#  SECTION 4.  VISUALIZATION ADAPTERS  (OPTIONAL LINK)
# ===================================================================
# This section simply re‑exports plotting functions for convenience.
# These functions are defined in `egm.reporting.visualizers.xeb_plotter`
# so that users can directly do:
#   from egm.core.analysis.xeb import plot_xeb_decay
# without needing to know internal module paths.

try:
    from egm.reporting.visualizers.xeb_plotter import plot_xeb_decay, plot_spb_decay
    __all__ = [
        "analyze_xeb_fidelity",
        "fit_xeb_decay",
        "analyze_xeb_and_spb_from_results",
        "plot_xeb_decay",
        "plot_spb_decay",
    ]
except ImportError:
    __all__ = [
        "analyze_xeb_fidelity",
        "fit_xeb_decay",
        "analyze_xeb_and_spb_from_results",
    ]
    logger.warning("xeb_plotter not found — visualization features disabled.")