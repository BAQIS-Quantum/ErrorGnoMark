# # File: errorgnomark/analysis/rb.py
# # ---------------------------------------------------------------------
# # Module: Randomized Benchmarking (RB) Analysis Utilities
# # ---------------------------------------------------------------------
# # Provides core analysis functions for fitting RB experimental data,
# # computing Error Per Clifford (EPC) and Error Per Gate (EPG), and
# # optionally generating fitted model data for visualization.
# #
# # This implementation is numerically stable and uses standardized
# # output fields compatible with reporting and visualization modules.
# # ---------------------------------------------------------------------

# from __future__ import annotations
# import numpy as np
# from scipy.optimize import curve_fit, OptimizeWarning
# from typing import Dict, Any, List
# import warnings
# import logging

# # ---------------------------------------------------------------------
# # Logging Configuration
# # ---------------------------------------------------------------------
# logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# # ---------------------------------------------------------------------
# # Helper Function
# # ---------------------------------------------------------------------
# def _rb_decay_function(m: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
#     """
#     Exponential decay model used for Randomized Benchmarking.

#     f(m) = A * p^m + B
#     """
#     return A * (p ** m) + B


# # ---------------------------------------------------------------------
# # Core Fitting Routine
# # ---------------------------------------------------------------------
# def fit_rb_data(
#     depths: List[int],
#     means: List[float],
#     stds: List[float],
#     num_qubits: int,
# ) -> Dict[str, Any]:
#     """
#     Perform a curve fit to Randomized Benchmarking data.

#     The function fits the measured survival probabilities to the model:
#         f(m) = A * p^m + B

#     and calculates the derived error-per-Clifford (EPC).

#     Args:
#         depths: Clifford sequence depths.
#         means: Mean survival probabilities at each depth.
#         stds: Standard errors corresponding to each mean.
#         num_qubits: Number of qubits in the experiment.

#     Returns:
#         Dictionary containing fit parameters and metadata fields:
#             {
#                 "fit_successful": bool,
#                 "x_data": [...],
#                 "y_data": [...],
#                 "y_err": [...],
#                 "params": {"A": float, "p": float, "B": float},
#                 "param_errors": {...},
#                 "epc": float,
#                 "p": float,
#                 "fit_x": np.ndarray,
#                 "fit_y": np.ndarray,
#                 "error_message": str,
#             }
#     """
#     d = 2 ** num_qubits
#     result: Dict[str, Any] = {
#         "fit_successful": False,
#         "x_data": depths,
#         "y_data": means,
#         "y_err": stds,
#         "params": {},
#         "param_errors": {},
#         "epc": None,
#         "p": None,
#         "fit_x": None,
#         "fit_y": None,
#         "error_message": "Fit not executed.",
#     }

#     # Initial parameter estimates
#     b_guess = 1.0 / d
#     a_guess = max(means[0] - b_guess, 0.0)
#     p_guess = 0.98
#     initial_guess = [a_guess, p_guess, b_guess]
#     bounds = ([0, 0, 0], [1, 1, 1])

#     with warnings.catch_warnings():
#         warnings.simplefilter("ignore", OptimizeWarning)
#         try:
#             popt, pcov = curve_fit(
#                 _rb_decay_function,
#                 xdata=depths,
#                 ydata=means,
#                 p0=initial_guess,
#                 sigma=stds,
#                 bounds=bounds,
#                 absolute_sigma=True,
#                 maxfev=10000,
#             )

#             perr = np.sqrt(np.diag(pcov))
#             param_names = ["A", "p", "B"]

#             result.update(
#                 {
#                     "fit_successful": True,
#                     "params": dict(zip(param_names, popt)),
#                     "param_errors": dict(zip(param_names, perr)),
#                     "p": popt[1],
#                     "epc": (d - 1) / d * (1 - popt[1]),
#                     "fit_x": np.linspace(min(depths), max(depths), 200),
#                     "fit_y": _rb_decay_function(
#                         np.linspace(min(depths), max(depths), 200), *popt
#                     ),
#                     "error_message": "",
#                 }
#             )

#             logging.info(
#                 f"RB fit successful: A={popt[0]:.3f}, p={popt[1]:.5f}, "
#                 f"B={popt[2]:.3f}, EPC={result['epc']:.3e}"
#             )

#         except (RuntimeError, ValueError) as err:
#             msg = f"RB fit failed: {err}"
#             result["error_message"] = msg
#             logging.warning(msg)

#     return result


# # ---------------------------------------------------------------------
# # EPG Calculation
# # ---------------------------------------------------------------------
# def calculate_epg(p_std: float, p_interleaved: float, num_qubits: int) -> float:
#     """
#     Compute the Error Per Gate (EPG) from standard and interleaved
#     decay parameters.

#     Args:
#         p_std: Decay parameter from the standard RB.
#         p_interleaved: Decay parameter from the interleaved RB.
#         num_qubits: Number of qubits tested.

#     Returns:
#         Calculated EPG value (float).
#     """
#     d = 2 ** num_qubits
#     if p_std <= 0:
#         logging.warning("Invalid standard RB parameter (p_std ≤ 0). Returning EPG = 1.0")
#         return 1.0
#     epg = (d - 1) / d * (1 - p_interleaved / (p_std + 1e-12))
#     return epg


# =============================================================================
# File: src/egm/core/analysis/rb.py
# Version: v5.0 – Unified RB Analysis (EGM-Standard + SISQ-Compatible)
# Author : OpenAI-Assistant
# =============================================================================
"""
Randomized Benchmarking (RB) Analysis Utilities — Unified EGM‑Standard Edition

This module merges the robust fitting and flexible input capabilities of
`sisq‑egm‑rb` with the clean, structured architecture of the EGM framework.

Features
--------
✔ Supports both list‑style and dict‑style data input.
✔ Automatically computes mean survival probabilities and standard errors.
✔ Includes R², EPC, and full parameter set (A, B, p) in output.
✔ Compatible with `x_axis_mode` (via optional gate‑count mapping).
✔ Standardized result dict usable by the EGM reporting module.
✔ Safe handling of ill‑conditioned datasets (graceful degradation).
"""

from __future__ import annotations

import numpy as np
import logging
import warnings
from typing import Dict, Any, List, Optional
from scipy.optimize import curve_fit, OptimizeWarning

# ---------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# ---------------------------------------------------------------------
# Default Constants
# ---------------------------------------------------------------------
_MAX_EVALS = 10000
_DEFAULT_P_GUESS = 0.99

# ---------------------------------------------------------------------
# Core Decay Model
# ---------------------------------------------------------------------
def _rb_decay_function(m: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """Standard RB model: f(m) = A · p^m + B."""
    return A * (p ** m) + B

# ---------------------------------------------------------------------
# Flexible RB Fit Routine
# ---------------------------------------------------------------------
def fit_rb_data(
    depths: Optional[List[int]] = None,
    means: Optional[List[float]] = None,
    stds: Optional[List[float]] = None,
    num_qubits: int = 1,
    survivals: Optional[Dict[int, List[float]]] = None,
    gate_counts: Optional[Dict[int, float]] = None,
) -> Dict[str, Any]:
    """
    Fit Randomized‑Benchmarking decay curves.

    Supports two input styles:
      (a) Explicit list mode: (depths, means, stds)
      (b) Dict mode: survivals = {depth: [values]}, auto‑aggregated.

    Args
    ----
    depths:        List of Clifford depths (used in explicit mode).
    means:         Mean survival probability per depth.
    stds:          Standard error of the mean per depth.
    num_qubits:    Number of qubits in the experiment.
    survivals:     Dictionary of raw survival samples by depth.
    gate_counts:   Optional mapping of physical‑gate count per depth.

    Returns
    -------
    Dict[str, Any]
        {
          "fit_successful": bool,
          "A": float, "B": float, "p": float,
          "epc": float, "r_squared": float,
          "depths": [...],
          "means": [...], "std_errors": [...],
          "gate_counts": [...],
          "fit_x": [...], "fit_y": [...],
          "message": str,
        }
    """
    # ------------------------------------------------------------------
    # Pre‑process Input Data
    # ------------------------------------------------------------------
    if survivals is not None:
        depths_arr = np.array(sorted(survivals.keys()), dtype=float)
        means_arr = np.array([np.mean(survivals[d]) for d in depths_arr])
        stds_arr = np.array([
            np.std(survivals[d], ddof=1) / np.sqrt(max(len(survivals[d]), 1))
            for d in depths_arr
        ])
    else:
        depths_arr = np.array(depths or [], dtype=float)
        means_arr = np.array(means or [], dtype=float)
        stds_arr = np.array(stds or [1.0]*len(means_arr), dtype=float)

    if len(depths_arr) < 3:
        return _result_failure("Insufficient data points (<3) for RB fit.")

    d = 2 ** num_qubits
    gate_array = (
        np.array([gate_counts.get(int(m), np.nan) for m in depths_arr])
        if gate_counts else np.full_like(depths_arr, np.nan)
    )

    # ------------------------------------------------------------------
    # Initial Guesses & Curve Fit
    # ------------------------------------------------------------------
    init = [1 - 1/d, _DEFAULT_P_GUESS, 1/d]
    bounds = ([0, 0, 0], [1, 1.0, 1])

    results = _init_result(depths_arr, means_arr, stds_arr, gate_array)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OptimizeWarning)
        try:
            popt, pcov = curve_fit(
                _rb_decay_function,
                depths_arr,
                means_arr,
                p0=init,
                sigma=stds_arr,
                bounds=bounds,
                absolute_sigma=True,
                maxfev=_MAX_EVALS,
            )
            A, p, B = popt
            perr = np.sqrt(np.diag(pcov))
            epc = ((d - 1) / d) * (1 - p)

            residuals = means_arr - _rb_decay_function(depths_arr, *popt)
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((means_arr - np.mean(means_arr)) ** 2)
            r_sq = 1 - ss_res / ss_tot if ss_tot > 1e-12 else np.nan

            fit_x = np.linspace(min(depths_arr), max(depths_arr), 200)
            fit_y = _rb_decay_function(fit_x, *popt)

            results.update({
                "fit_successful": True,
                "A": float(A),
                "B": float(B),
                "p": float(p),
                "epc": float(epc),
                "r_squared": float(r_sq),
                "fit_x": fit_x.tolist(),
                "fit_y": fit_y.tolist(),
                "message": "Fit successful.",
            })
            logging.info(
                f"[RB‑FIT] Success: A={A:.3f}, p={p:.5f}, B={B:.3f}, "
                f"EPC={epc:.3e}, R²={r_sq:.4f}"
            )

        except Exception as exc:
            results["message"] = f"Fit failed: {exc!s}"
            logging.warning(results["message"])

    return results

# ---------------------------------------------------------------------
# Error per Gate Calculation
# ---------------------------------------------------------------------
def calculate_epg(p_std: float, p_interleaved: float, num_qubits: int) -> float:
    """Compute Error Per Gate (EPG) using standard and interleaved p."""
    d = 2 ** num_qubits
    if p_std <= 0:
        logging.warning("Invalid p_std ≤ 0; returning EPG = 1.0")
        return 1.0
    epg = ((d - 1) / d) * (1 - p_interleaved / (p_std + 1e-12))
    return float(epg)

# ---------------------------------------------------------------------
# Helper Constructors
# ---------------------------------------------------------------------
def _init_result(depths, means, stds, gate_array):
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
        "gate_counts": gate_array.tolist(),
        "fit_x": [],
        "fit_y": [],
        "message": "Not fitted.",
    }

def _result_failure(msg: str) -> Dict[str, Any]:
    logging.warning(f"[RB‑FIT] {msg}")
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
        "gate_counts": [],
        "fit_x": [],
        "fit_y": [],
        "message": msg,
    }

# =============================================================================
# End of File
# =============================================================================