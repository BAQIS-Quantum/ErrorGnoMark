# =============================================================================
# File    : egm/core/analysis/xeb.py
# Version : v5.2.0 – RB-Schema + SISQ-Enhanced Error-Bar Edition
# Author  : OpenAI-Assistant
# =============================================================================
"""
Cross-Entropy Benchmarking (XEB) Analysis and Unified SPB Integration
=====================================================================

Integrates normalized Google-style fidelity analysis (SISQ logic)
with the EGM v5 RB-schema exponential-decay fitting.

✓ RB-schema compatible outputs (A, B, p, epc, r_squared)
✓ Unified joint analysis with SPB using egm.core.analysis.spb
✓ Fully modular — for both simulation and experimental data
✓ SISQ-EGM style selectable error-bar computation:
  "sem", "std", "range", "bootstrap", "none"
"""

from __future__ import annotations
import numpy as np
import logging
import warnings
from collections import defaultdict
from typing import Dict, Any, List, Tuple, Optional
from scipy.optimize import curve_fit, OptimizeWarning

from egm.analysis.spb import analyze_speckle_purity, fit_spb_data

# -------------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

_MAX_EVALS = 10000
_DEFAULT_P_GUESS = 0.995

# =============================================================================
# 1. Normalized Cross-Entropy Fidelity
# =============================================================================
def analyze_xeb_fidelity(
    ideal_probs: Dict[str, float],
    noisy_counts: Dict[str, float],
    num_qubits: int,
) -> float:
    """
    Compute normalized XEB fidelity following Google's definition:

        F_XEB = (Σ_x p_ideal(x)p_exp(x) - 1/2ⁿ)
                / (Σ_x p_ideal(x)² - 1/2ⁿ)
    """
    if not ideal_probs or not noisy_counts:
        return 0.0

    total = float(sum(noisy_counts.values()))
    if total <= 0.0:
        return 0.0

    d = 2 ** num_qubits

    # Normalize noisy counts to probabilities if necessary
    if total > 1.0 + 1e-9:
        p_exp = {k: v / total for k, v in noisy_counts.items()}
    else:
        p_exp = noisy_counts

    exp_dot = sum(ideal_probs.get(k, 0.0) * p_exp.get(k, 0.0) for k in ideal_probs.keys())
    exp_ideal = sum(p ** 2 for p in ideal_probs.values())

    denom = exp_ideal - 1 / d
    if denom <= 0.0:
        return 0.0

    f_xeb = (exp_dot - 1 / d) / denom
    return float(np.clip(f_xeb, -0.2, 1.0))

# =============================================================================
# 2. Exponential Decay Fit (RB-Schema + Error Bar Support)
# =============================================================================
def _xeb_decay_function(x: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """Exponential model f(x) = A * p^x + B."""
    return A * (p ** x) + B


def _compute_error(values: List[float], mode: str = "sem") -> float:
    """
    Compute SISQ-EGM style error bar for a list of fidelities.
    Modes: 'sem' / 'std' / 'range' / 'bootstrap' / 'none'
    """
    arr = np.asarray(values, float)
    n = len(arr)
    if n <= 1:
        return 0.0

    if mode == "sem":
        return float(np.std(arr, ddof=1) / np.sqrt(n))
    if mode == "std":
        return float(np.std(arr, ddof=1))
    if mode == "range":
        return float((np.max(arr) - np.min(arr)) / 2.0)
    if mode == "bootstrap":
        rng = np.random.default_rng(42)
        boots = [np.mean(rng.choice(arr, n, replace=True)) for _ in range(800)]
        low, high = np.percentile(boots, [16, 84])
        return float((high - low) / 2.0)
    return 0.0


def fit_xeb_data(
    fidelities: Optional[Dict[int, List[float]]] = None,
    depths: Optional[List[int]] = None,
    means: Optional[List[float]] = None,
    stds: Optional[List[float]] = None,
    num_qubits: int = 1,
    error_bar_mode: str = "sem",
) -> Dict[str, Any]:
    """
    Fit XEB data to f(x) = A * p^x + B (EGM RB-schema),
    with optional SISQ-EGM style error-bar support.
    """
    if fidelities is not None:
        depths_arr = np.array(sorted(fidelities.keys()), dtype=float)
        means_arr = np.array([np.mean(fidelities[d]) for d in depths_arr])
        stds_arr = np.array(
            [_compute_error(fidelities[d], error_bar_mode) for d in depths_arr],
            dtype=float,
        )
    else:
        depths_arr = np.array(depths or [], dtype=float)
        means_arr = np.array(means or [], dtype=float)
        stds_arr = np.array(stds or [1.0] * len(means_arr), dtype=float)

    if len(depths_arr) < 3:
        return _result_failure("Insufficient points (<3) for XEB fit.")

    d = 2 ** num_qubits
    result = _init_result(depths_arr, means_arr, stds_arr)

    init = [1 - 1 / d, _DEFAULT_P_GUESS, 1 / d]
    bounds = ([0, 0, -0.5], [2, 1, 0.5])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OptimizeWarning)
        try:
            popt, _ = curve_fit(
                _xeb_decay_function,
                depths_arr,
                means_arr,
                p0=init,
                sigma=np.maximum(stds_arr, 1e-6),
                bounds=bounds,
                absolute_sigma=True,
                maxfev=_MAX_EVALS,
            )
            A, p, B = popt
            epc = ((d - 1) / d) * (1 - p)

            residuals = means_arr - _xeb_decay_function(depths_arr, *popt)
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((means_arr - np.mean(means_arr)) ** 2)
            r_sq = 1 - ss_res / ss_tot if ss_tot > 1e-12 else np.nan

            fit_x = np.linspace(min(depths_arr), max(depths_arr), 200)
            fit_y = _xeb_decay_function(fit_x, *popt)

            result.update(
                {
                    "fit_successful": True,
                    "A": float(A),
                    "B": float(B),
                    "p": float(p),
                    "epc": float(epc),
                    "r_squared": float(r_sq),
                    "fit_x": fit_x.tolist(),
                    "fit_y": fit_y.tolist(),
                    "message": "Fit successful.",
                }
            )
            logger.info(
                f"[XEB-FIT] A={A:.3f}, p={p:.6f}, B={B:.3f}, "
                f"EPC={epc:.3e}, R²={r_sq:.4f}"
            )

        except Exception as exc:
            logger.warning(f"[XEB-FIT] Fit failed: {exc!s}")
            result["message"] = f"Fit failed: {exc!s}"

    return result


def _init_result(depths, means, stds):
    """Initialize RB-schema result field layout."""
    return {
        "fit_successful": False,
        "A": np.nan,
        "B": np.nan,
        "p": np.nan,
        "epc": np.nan,
        "r_squared": np.nan,
        "depths": depths.tolist(),
        "means": means.tolist(),
        "std_errors": stds.tolist(),
        "fit_x": [],
        "fit_y": [],
        "message": "Not fitted.",
    }


def _result_failure(msg: str) -> Dict[str, Any]:
    """Return standardized failure result dictionary."""
    return {
        "fit_successful": False,
        "A": np.nan,
        "B": np.nan,
        "p": np.nan,
        "epc": np.nan,
        "r_squared": np.nan,
        "depths": [],
        "means": [],
        "std_errors": [],
        "fit_x": [],
        "fit_y": [],
        "message": msg,
    }

# =============================================================================
# 3. Unified Joint XEB + SPB Analysis (With Error Bars)
# =============================================================================
def analyze_xeb_and_spb_from_results(
    results_by_depth: Dict[int, List[Tuple[Dict[str, float], Dict[str, float]]]],
    num_qubits: int,
    circuits: Optional[List[Any]] = None,
    axis_mode: str = "depth",
    error_bar_mode: str = "sem",
) -> Dict[str, Any]:
    """
    Perform unified XEB + SPB analysis (SISQ-enhanced).

    Parameters
    ----------
    results_by_depth : Dict[int, List[Tuple[Dict, Dict]]]
        {depth: [(ideal_probs, noisy_counts), ...]}.
    num_qubits : int
        Number of qubits (circuit width).
    circuits : List[Any], optional
        Circuits (for gate-count mapping, if needed).
    axis_mode : str
        "depth" or "gate_count".
    error_bar_mode : str
        "sem" / "std" / "range" / "bootstrap" / "none".

    Returns
    -------
    Dict[str, Any]
        {
          "xeb_analysis": {"raw_data": fidelities_by_x, "fit_results": fit_dict},
          "spb_analysis": {"raw_data": purities_by_x, "fit_results": fit_dict},
          "axis_mode": axis_mode
        }
    """
    remap = {d: d for d in results_by_depth.keys()}
    fidelities_by_x, purities_by_x = defaultdict(list), defaultdict(list)

    # Compute per-circuit XEB & SPB values
    for depth, pairs in results_by_depth.items():
        x_val = remap.get(depth, depth)
        for ideal, noisy in pairs:
            f_val = analyze_xeb_fidelity(ideal, noisy, num_qubits)
            p_val = analyze_speckle_purity(ideal, noisy, num_qubits)
            fidelities_by_x[x_val].append(f_val)
            purities_by_x[x_val].append(p_val)

    # Fit both datasets with error-bar aware fitting
    xeb_fit = fit_xeb_data(
        fidelities=fidelities_by_x,
        num_qubits=num_qubits,
        error_bar_mode=error_bar_mode,
    )
    spb_fit = fit_spb_data(purities=purities_by_x, num_qubits=num_qubits)

    return {
        "xeb_analysis": {"raw_data": fidelities_by_x, "fit_results": xeb_fit},
        "spb_analysis": {"raw_data": purities_by_x, "fit_results": spb_fit},
        "axis_mode": axis_mode,
    }