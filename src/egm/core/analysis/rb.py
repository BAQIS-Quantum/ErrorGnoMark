# File: errorgnomark/analysis/rb.py
# ---------------------------------------------------------------------
# Module: Randomized Benchmarking (RB) Analysis Utilities
# ---------------------------------------------------------------------
# Provides core analysis functions for fitting RB experimental data,
# computing Error Per Clifford (EPC) and Error Per Gate (EPG), and
# optionally generating fitted model data for visualization.
#
# This implementation is numerically stable and uses standardized
# output fields compatible with reporting and visualization modules.
# ---------------------------------------------------------------------

from __future__ import annotations
import numpy as np
from scipy.optimize import curve_fit, OptimizeWarning
from typing import Dict, Any, List
import warnings
import logging

# ---------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# ---------------------------------------------------------------------
# Helper Function
# ---------------------------------------------------------------------
def _rb_decay_function(m: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """
    Exponential decay model used for Randomized Benchmarking.

    f(m) = A * p^m + B
    """
    return A * (p ** m) + B


# ---------------------------------------------------------------------
# Core Fitting Routine
# ---------------------------------------------------------------------
def fit_rb_data(
    depths: List[int],
    means: List[float],
    stds: List[float],
    num_qubits: int,
) -> Dict[str, Any]:
    """
    Perform a curve fit to Randomized Benchmarking data.

    The function fits the measured survival probabilities to the model:
        f(m) = A * p^m + B

    and calculates the derived error-per-Clifford (EPC).

    Args:
        depths: Clifford sequence depths.
        means: Mean survival probabilities at each depth.
        stds: Standard errors corresponding to each mean.
        num_qubits: Number of qubits in the experiment.

    Returns:
        Dictionary containing fit parameters and metadata fields:
            {
                "fit_successful": bool,
                "x_data": [...],
                "y_data": [...],
                "y_err": [...],
                "params": {"A": float, "p": float, "B": float},
                "param_errors": {...},
                "epc": float,
                "p": float,
                "fit_x": np.ndarray,
                "fit_y": np.ndarray,
                "error_message": str,
            }
    """
    d = 2 ** num_qubits
    result: Dict[str, Any] = {
        "fit_successful": False,
        "x_data": depths,
        "y_data": means,
        "y_err": stds,
        "params": {},
        "param_errors": {},
        "epc": None,
        "p": None,
        "fit_x": None,
        "fit_y": None,
        "error_message": "Fit not executed.",
    }

    # Initial parameter estimates
    b_guess = 1.0 / d
    a_guess = max(means[0] - b_guess, 0.0)
    p_guess = 0.98
    initial_guess = [a_guess, p_guess, b_guess]
    bounds = ([0, 0, 0], [1, 1, 1])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OptimizeWarning)
        try:
            popt, pcov = curve_fit(
                _rb_decay_function,
                xdata=depths,
                ydata=means,
                p0=initial_guess,
                sigma=stds,
                bounds=bounds,
                absolute_sigma=True,
                maxfev=10000,
            )

            perr = np.sqrt(np.diag(pcov))
            param_names = ["A", "p", "B"]

            result.update(
                {
                    "fit_successful": True,
                    "params": dict(zip(param_names, popt)),
                    "param_errors": dict(zip(param_names, perr)),
                    "p": popt[1],
                    "epc": (d - 1) / d * (1 - popt[1]),
                    "fit_x": np.linspace(min(depths), max(depths), 200),
                    "fit_y": _rb_decay_function(
                        np.linspace(min(depths), max(depths), 200), *popt
                    ),
                    "error_message": "",
                }
            )

            logging.info(
                f"RB fit successful: A={popt[0]:.3f}, p={popt[1]:.5f}, "
                f"B={popt[2]:.3f}, EPC={result['epc']:.3e}"
            )

        except (RuntimeError, ValueError) as err:
            msg = f"RB fit failed: {err}"
            result["error_message"] = msg
            logging.warning(msg)

    return result


# ---------------------------------------------------------------------
# EPG Calculation
# ---------------------------------------------------------------------
def calculate_epg(p_std: float, p_interleaved: float, num_qubits: int) -> float:
    """
    Compute the Error Per Gate (EPG) from standard and interleaved
    decay parameters.

    Args:
        p_std: Decay parameter from the standard RB.
        p_interleaved: Decay parameter from the interleaved RB.
        num_qubits: Number of qubits tested.

    Returns:
        Calculated EPG value (float).
    """
    d = 2 ** num_qubits
    if p_std <= 0:
        logging.warning("Invalid standard RB parameter (p_std ≤ 0). Returning EPG = 1.0")
        return 1.0
    epg = (d - 1) / d * (1 - p_interleaved / (p_std + 1e-12))
    return epg