# =============================================================================
# File    : egm/core/analysis/spb.py
# Version : v5.2.0 – RB-Schema + SISQ Error-Bar Edition
# Author  : OpenAI-Assistant
# =============================================================================
"""
State-Purity Benchmarking (SPB) Analysis – RB-Schema + SISQ Error-Bar Logic
===========================================================================

This version unifies EGM v5.0’s RB-schema output with the SISQ-EGM v4.3.2
enhanced error-bar computation and purity metric definition.

✔ RB-Schema compatible: same output fields as XEB/SPB fittings
✔ Supports selectable error-bar modes: "sem", "std", "range", "bootstrap", "none"
✔ Backward-compatible API (functions and return keys unchanged)
"""

from __future__ import annotations
import numpy as np
import logging
import warnings
from typing import Dict, Any, List, Optional
from scipy.optimize import curve_fit, OptimizeWarning

# -------------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

_MAX_EVALS = 10000
_DEFAULT_P_GUESS = 0.99

# =============================================================================
# 1️⃣  Normalized Speckle-Purity Metric (SISQ-Enhanced)
# =============================================================================
def analyze_speckle_purity(
    ideal_probs: Dict[str, float],
    noisy_counts: Dict[str, Any],
    num_qubits: int = 1,
) -> float:
    """
    Compute normalized Speckle-Purity (SPB):

        P_SPB = Σ_x [p_exp(x)^2] / Σ_x [p_ideal(x)^2]

    Compatible with SISQ v4.x logic, automatically handling
    raw counts or normalized probabilities.
    """
    if not ideal_probs or not noisy_counts:
        return np.nan

    total = float(sum(noisy_counts.values()))
    if total <= 0.0:
        return np.nan

    # Normalize if input are counts
    if total > 1.0 + 1e-9:
        p_exp = {k: float(v) / total for k, v in noisy_counts.items()}
    else:
        p_exp = {k: float(v) for k, v in noisy_counts.items()}

    keys = set(ideal_probs.keys()) | set(p_exp.keys())
    p_ideal = np.array([ideal_probs.get(k, 0.0) for k in keys], float)
    p_expv = np.array([p_exp.get(k, 0.0) for k in keys], float)

    denom = np.sum(p_ideal**2)
    if denom <= 0.0:
        return np.nan
    purity = np.sum(p_expv**2) / denom
    return float(np.clip(purity, 0.0, 1.0))

# =============================================================================
# 2️⃣  Error-Bar Utility (identical to SISQ logic)
# =============================================================================
def _compute_error(values: List[float], mode: str = "sem") -> float:
    """Compute representative error-bar size for sample values."""
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

# =============================================================================
# 3️⃣  Exponential Decay Fit (RB-Schema + Error Bars)
# =============================================================================
def _spb_decay_function(x: np.ndarray, A: float, p_c: float, B: float) -> np.ndarray:
    """Exponential SPB model f(x) = A*(p_c)^x + B."""
    return A * (p_c**x) + B


def fit_spb_data(
    purities: Optional[Dict[int, List[float]]] = None,
    depths: Optional[List[int]] = None,
    means: Optional[List[float]] = None,
    stds: Optional[List[float]] = None,
    num_qubits: int = 1,
    error_bar_mode: str = "sem",
) -> Dict[str, Any]:
    """
    Fit SPB decay to f(x)=A*(p_c)^x + B (RB-Schema output),
    supporting SISQ error-bar computation ("sem"/"std"/"range"/"bootstrap"/"none").
    """
    if purities is not None:
        depths_arr = np.array(sorted(purities.keys()), float)
        means_arr = np.array([np.mean(purities[d]) for d in depths_arr])
        stds_arr = np.array(
            [_compute_error(purities[d], mode=error_bar_mode) for d in depths_arr]
        )
    else:
        depths_arr = np.array(depths or [], float)
        means_arr = np.array(means or [], float)
        stds_arr = np.array(stds or [1.0] * len(means_arr), float)

    if len(depths_arr) < 3:
        return _result_failure("Insufficient points (<3) for SPB fit.")

    result = _init_result(depths_arr, means_arr, stds_arr)

    init = [0.9, _DEFAULT_P_GUESS, 0.05]
    bounds = ([0, 0, 0], [1.5, 1.0, 1.0])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OptimizeWarning)
        try:
            popt, _ = curve_fit(
                _spb_decay_function,
                depths_arr,
                means_arr,
                p0=init,
                sigma=np.maximum(stds_arr, 1e-6),
                bounds=bounds,
                absolute_sigma=True,
                maxfev=_MAX_EVALS,
            )
            A, p_c, B = popt

            residuals = means_arr - _spb_decay_function(depths_arr, *popt)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((means_arr - np.mean(means_arr))**2)
            r_sq = 1 - ss_res / ss_tot if ss_tot > 1e-12 else np.nan

            fit_x = np.linspace(float(min(depths_arr)), float(max(depths_arr)), 200)
            fit_y = _spb_decay_function(fit_x, *popt)

            result.update(
                {
                    "fit_successful": True,
                    "A": float(A),
                    "B": float(B),
                    "p_c": float(p_c),
                    "r_squared": float(r_sq),
                    "fit_x": fit_x.tolist(),
                    "fit_y": fit_y.tolist(),
                    "message": "Fit successful.",
                }
            )
            logging.info(
                f"[SPB-FIT] A={A:.3f}, p_c={p_c:.5f}, B={B:.3f}, R²={r_sq:.4f}"
            )

        except Exception as exc:
            logging.warning(f"[SPB-FIT] Fit failed: {exc!s}")
            result["message"] = f"Fit failed: {exc!s}"

    return result


def _init_result(depths, means, stds):
    """Initialize standard RB-Schema dictionary."""
    return {
        "fit_successful": False,
        "A": np.nan,
        "B": np.nan,
        "p_c": np.nan,
        "r_squared": np.nan,
        "depths": depths.tolist(),
        "means": means.tolist(),
        "std_errors": stds.tolist(),
        "fit_x": [],
        "fit_y": [],
        "message": "Not fitted.",
    }


def _result_failure(msg: str) -> Dict[str, Any]:
    """Generate failure result dictionary."""
    logging.warning(f"[SPB-FIT] {msg}")
    return {
        "fit_successful": False,
        "A": np.nan,
        "B": np.nan,
        "p_c": np.nan,
        "r_squared": np.nan,
        "depths": [],
        "means": [],
        "std_errors": [],
        "fit_x": [],
        "fit_y": [],
        "message": msg,
    }