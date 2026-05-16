# # File Path: errorgnomark/analysis/prb.py
# # [FINAL VERSION - Implemented robust fitting and correct calibration]

# """
# Module for analyzing Purity Randomized Benchmarking (PRB) experiments.

# This module provides functions for fitting PRB decay data, calculating interleaved
# gate error, and generating plots for visualization. The key feature is a robust
# fitting strategy that first fits the raw purity data to the model P(m) = A * alpha^m + B,
# and then uses the fitted A and B parameters to calibrate the data for clear
# visualization and interpretation of the decay parameter 'alpha'.
# """

# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.optimize import curve_fit
# from typing import Dict, List, Tuple, TypedDict, Optional

# # --- Type Definitions for Clarity ---

# class PRBFitResult(TypedDict):
#     """
#     Defines the structure for the results of a PRB data fit.
#     """
#     fit_successful: bool
#     A: float
#     B: float
#     alpha: float
#     params: Tuple[float, float, float]
#     param_errors: Tuple[float, float, float]
#     depths: List[int]
#     calibrated_mean_purities: List[float]
#     calibrated_std_errors: List[float]
#     raw_mean_purities: List[float]

# class GateErrorResult(TypedDict):
#     """
#     Defines the structure for the result of a gate error calculation.
#     """
#     gate_error: float
#     calculation_successful: bool

# # --- Core Analysis Functions ---

# def _prb_decay_model(m: np.ndarray, A: float, B: float, alpha: float) -> np.ndarray:
#     """
#     The exponential decay model for Purity Randomized Benchmarking.

#     The model is P(m) = A * alpha^m + B, where:
#       - m: The sequence depth (number of Cliffords).
#       - A: Amplitude, related to state preparation and measurement (SPAM) quality.
#       - B: Asymptotic purity, ideally 1/d for a fully depolarized state.
#       - alpha: The decay parameter, related to the average fidelity of a Clifford.

#     Args:
#         m: An array of sequence depths.
#         A: The amplitude parameter.
#         B: The offset or asymptotic purity parameter.
#         alpha: The decay parameter.

#     Returns:
#         An array of calculated purities based on the model.
#     """
#     return A * (alpha**m) + B

# def fit_prb_data(purities: Dict[int, List[float]], num_qubits: int) -> PRBFitResult:
#     """
#     Fits Purity RB data to the exponential decay model using a robust method.

#     This function first fits the raw purity data to P(m) = A * alpha^m + B.
#     It then uses the fitted A and B parameters to calibrate the purity data
#     for visualization, where the calibrated data should approximate alpha^m.

#     Args:
#         purities: A dictionary mapping sequence depth (int) to a list of
#                   measured purities (float) for that depth.
#         num_qubits: The number of qubits in the experiment.

#     Returns:
#         A PRBFitResult dictionary containing the fit status, parameters,
#         errors, and both calibrated and raw purity data.
#     """
#     valid_depths = sorted([d for d in purities if purities.get(d)])
    
#     # At least 3 data points are needed to reliably fit 3 parameters (A, B, alpha).
#     if len(valid_depths) < 3:
#         return _create_prb_failure_result(purities, valid_depths)

#     depths = np.array(valid_depths)
#     mean_purities = np.array([np.mean(purities[d]) for d in depths])
#     # Use sample standard deviation (ddof=1) for an unbiased estimate.
#     std_errors = np.array([
#         np.std(purities[d], ddof=1) / np.sqrt(len(purities[d])) if len(purities[d]) > 1 else 0.0
#         for d in depths
#     ])
#     # Prevent division by zero in the fitter for points with no variance.
#     std_errors[std_errors == 0] = 1e-9

#     try:
#         # --- Robust Fitting of Raw Data ---
#         # Provide educated initial guesses for the fitting parameters [A, B, alpha].
#         # Guess B (asymptote) from the last few data points.
#         B_guess = np.mean(mean_purities[-2:]) if len(mean_purities) > 1 else mean_purities[-1]
#         # Guess A (amplitude) as the difference between the start and the asymptote.
#         A_guess = mean_purities[0] - B_guess
#         # Guess alpha as a typical high-fidelity decay parameter.
#         alpha_guess = 0.99
#         p0 = [A_guess, B_guess, alpha_guess]
        
#         # Define physical bounds for the parameters. alpha must be in [0, 1].
#         bounds = ([-np.inf, 0.0, 0.0], [np.inf, np.inf, 1.0])

#         popt, pcov = curve_fit(
#             _prb_decay_model,
#             depths,
#             mean_purities,
#             p0=p0,
#             sigma=std_errors,
#             absolute_sigma=True,
#             bounds=bounds,
#             maxfev=10000,
#             check_finite=True
#         )
#         A, B, alpha = popt
#         param_errors = np.sqrt(np.diag(pcov))
        
#         # --- Post-Fit Calibration (for visualization) ---
#         # Calibrated purity y' = (y - B_fit) / A_fit, which should approximate alpha^m.
#         # This isolates the decay from SPAM-related offsets and scaling.
#         if abs(A) < 1e-9:  # Avoid division by zero if amplitude is negligible.
#             calibrated_purities = mean_purities
#             calibrated_std_errors = std_errors
#         else:
#             calibrated_purities = (mean_purities - B) / A
#             calibrated_std_errors = std_errors / abs(A)

#         return {
#             'fit_successful': True,
#             'A': A, 'B': B, 'alpha': alpha,
#             'params': tuple(popt),
#             'param_errors': tuple(param_errors),
#             'depths': depths.tolist(),
#             'calibrated_mean_purities': calibrated_purities.tolist(),
#             'calibrated_std_errors': calibrated_std_errors.tolist(),
#             'raw_mean_purities': mean_purities.tolist(),
#         }

#     except (RuntimeError, ValueError):
#         # Fit failed, return a structured failure response.
#         return _create_prb_failure_result(purities, valid_depths)

# def calculate_prb_gate_error(
#     std_results: PRBFitResult,
#     int_results: PRBFitResult,
#     num_qubits: int
# ) -> GateErrorResult:
#     """
#     Calculates the interleaved gate error from standard and interleaved PRB results.

#     The error of the interleaved gate is determined by comparing the decay rates
#     of the standard and interleaved experiments.
#     Formula: r_g = ((d-1)/d) * (1 - alpha_interleaved / alpha_standard)

#     Args:
#         std_results: The PRBFitResult from the standard RB experiment.
#         int_results: The PRBFitResult from the interleaved RB experiment.
#         num_qubits: The number of qubits.

#     Returns:
#         A GateErrorResult dictionary with the calculated error and success status.
#     """
#     if std_results.get('fit_successful') and int_results.get('fit_successful'):
#         alpha_std = std_results['alpha']
#         alpha_int = int_results['alpha']
        
#         dimension = 2**num_qubits
#         error_factor = (dimension - 1) / dimension
        
#         # Prevent division by zero if standard decay is zero or fit is bad.
#         if abs(alpha_std) < 1e-9:
#             return {'gate_error': np.nan, 'calculation_successful': False}

#         gate_error = error_factor * (1 - alpha_int / alpha_std)
#         return {'gate_error': gate_error, 'calculation_successful': True}
        
#     return {'gate_error': np.nan, 'calculation_successful': False}

# # --- Plotting Functions ---

# def plot_prb_single(results: PRBFitResult, num_qubits: int):
#     """
#     Plots a single PRB decay curve using calibrated data and the fit.

#     Args:
#         results: A PRBFitResult dictionary from a single PRB experiment.
#         num_qubits: The number of qubits, for titling.
#     """
#     plt.style.use('seaborn-v0_8-whitegrid')
#     plt.figure(figsize=(10, 6))
    
#     plt.errorbar(
#         results['depths'], results['calibrated_mean_purities'],
#         yerr=results['calibrated_std_errors'],
#         fmt='o', color='steelblue', ecolor='lightsteelblue', capsize=5,
#         label='Purity Data (Calibrated)'
#     )
    
#     if results['fit_successful']:
#         alpha = results['alpha']
#         # For calibrated data, the fit curve is simply y = alpha^m.
#         fine_depths = np.linspace(0, max(results['depths']) if results['depths'] else 0, 200)
#         fit_curve = alpha**fine_depths
#         plt.plot(fine_depths, fit_curve, color='orangered', linestyle='--',
#                  label=f'Fit: $y = \\alpha^m$\n$\\alpha$ = {alpha:.4f}')

#     plt.xlabel("Clifford Depth (m)", fontsize=12)
#     plt.ylabel("Calibrated Purity: (Purity - B) / A", fontsize=12)
#     plt.title(f"Standard {num_qubits}-Qubit Purity RB", fontsize=14, pad=15)
#     plt.legend(fontsize=11)
#     plt.ylim(-0.1, 1.1)
#     plt.tight_layout()
#     plt.show()

# def plot_prb_comparison(
#     std_results: PRBFitResult,
#     int_results: PRBFitResult,
#     num_qubits: int,
#     target_gate_name: str
# ):
#     """
#     Plots standard and interleaved PRB decay curves on the same axes.

#     Args:
#         std_results: The PRBFitResult from the standard RB experiment.
#         int_results: The PRBFitResult from the interleaved RB experiment.
#         num_qubits: The number of qubits.
#         target_gate_name: The name of the interleaved gate for the plot title.
#     """
#     plt.style.use('seaborn-v0_8-whitegrid')
#     plt.figure(figsize=(10, 6))
    
#     gate_error_results = calculate_prb_gate_error(std_results, int_results, num_qubits)
#     gate_error = gate_error_results['gate_error']
    
#     # Plot Standard PRB data and fit
#     plt.errorbar(
#         std_results['depths'], std_results['calibrated_mean_purities'],
#         yerr=std_results['calibrated_std_errors'],
#         fmt='o', color='blue', ecolor='lightblue', capsize=5, label='Standard Data'
#     )
#     if std_results['fit_successful']:
#         fine_depths = np.linspace(0, max(std_results['depths']) if std_results['depths'] else 0, 200)
#         fit_curve = std_results['alpha']**fine_depths
#         plt.plot(fine_depths, fit_curve, color='blue', linestyle='--',
#                  label=f'Standard Fit ($\\alpha_{{std}}$={std_results["alpha"]:.4f})')

#     # Plot Interleaved PRB data and fit
#     plt.errorbar(
#         int_results['depths'], int_results['calibrated_mean_purities'],
#         yerr=int_results['calibrated_std_errors'],
#         fmt='s', color='red', ecolor='lightcoral', capsize=5, label='Interleaved Data'
#     )
#     if int_results['fit_successful']:
#         fine_depths = np.linspace(0, max(int_results['depths']) if int_results['depths'] else 0, 200)
#         fit_curve = int_results['alpha']**fine_depths
#         plt.plot(fine_depths, fit_curve, color='red', linestyle='--',
#                  label=f'Interleaved Fit ($\\alpha_{{int}}$={int_results["alpha"]:.4f})')

#     plt.xlabel("Clifford Depth (m)", fontsize=12)
#     plt.ylabel("Calibrated Purity: (Purity - B) / A", fontsize=12)
    
#     title = f"Interleaved Purity RB: '{target_gate_name.upper()}' on {num_qubits} Qubit(s)\n"
#     if gate_error_results['calculation_successful']:
#         title += f"Estimated Gate Error = {gate_error:.2e}"
#     else:
#         title += "Gate Error Calculation Failed"
#     plt.title(title, fontsize=14, pad=15)
    
#     plt.legend(fontsize=11)
#     plt.ylim(-0.1, 1.1)
#     plt.tight_layout()
#     plt.show()

# # --- Helper Functions ---

# def _create_prb_failure_result(
#     purities: Dict[int, List[float]],
#     depths: List[int]
# ) -> PRBFitResult:
#     """Helper to generate a structured dictionary for a failed PRB fit."""
#     nan_tuple = (np.nan, np.nan, np.nan)
#     raw_means = [np.mean(purities[d]) for d in depths if purities.get(d)]
#     raw_stds = [np.std(purities[d], ddof=1) for d in depths if purities.get(d)]
    
#     return {
#         'fit_successful': False,
#         'A': np.nan, 'B': np.nan, 'alpha': np.nan,
#         'params': nan_tuple,
#         'param_errors': nan_tuple,
#         'depths': depths,
#         'calibrated_mean_purities': raw_means,  # Fallback to raw data
#         'calibrated_std_errors': raw_stds, # Fallback to raw std dev
#         'raw_mean_purities': raw_means,
#     }


# =============================================================================
# File: src/egm/core/analysis/prb.py
# Version: v5.1 – Unified Purity RB Analysis (EGM-Compatible + Preprocessing API)
# Author : OpenAI‑Assistant
# =============================================================================
"""
Purity Randomized Benchmarking (PRB) — Analysis Utilities

Enhanced, robust fitting module using exponential model:
    P(m) = A · α^m + B

Features
--------
✔ Robust fitting with bounds & covariance.
✔ Automatic calibration – normalize (P−B)/A.
✔ Structured outputs aligned with `fit_rb_data`.
✔ Supports interleaved PRB error computation.
✔ Adds preprocessing utility for purity extraction from raw counts.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, TypedDict

import numpy as np
from scipy.optimize import curve_fit


# ---------------------------------------------------------------------
# Type Annotations
# ---------------------------------------------------------------------
class PRBFitResult(TypedDict):
    fit_successful: bool
    A: float
    B: float
    alpha: float
    params: Tuple[float, float, float]
    param_errors: Tuple[float, float, float]
    depths: List[int]
    calibrated_mean_purities: List[float]
    calibrated_std_errors: List[float]
    raw_mean_purities: List[float]

class GateErrorResult(TypedDict):
    gate_error: float
    calculation_successful: bool

# ---------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------
def _prb_decay_model(m: np.ndarray, A: float, B: float, alpha: float) -> np.ndarray:
    """PRB decay model: P(m)=A · α^m + B"""
    return A * (alpha ** m) + B

# ---------------------------------------------------------------------
# Preprocessing Utility  ✅ 新增
# ---------------------------------------------------------------------
def compute_purity_from_counts(
    counts: Dict[str, float],
    num_qubits: int
) -> float:
    """
    Convert raw measurement counts into dimension‑normalized purity value.

    Formula:
        P = d/(d−1) * (Σ p_i² − 1/d)

    where d = 2^num_qubits,  p_i are outcome probabilities.
    Returns a purity in [0, 1] consistent with PRB model.
    """
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    probs = np.array(list(counts.values()), dtype=float) / total
    purity_raw = float(np.sum(probs ** 2))
    d = 2 ** num_qubits
    purity_norm = (d / (d - 1)) * (purity_raw - 1 / d)
    return float(np.clip(purity_norm, 0.0, 1.0))

# ---------------------------------------------------------------------
# Fit Routine
# ---------------------------------------------------------------------
def fit_prb_data(purities: Dict[int, List[float]], num_qubits: int) -> PRBFitResult:
    """Fit Purity RB data and return calibrated values."""
    valid_depths = sorted([d for d in purities if purities.get(d)])
    if len(valid_depths) < 3:
        return _create_prb_failure_result(purities, valid_depths)

    depths = np.array(valid_depths, dtype=float)
    means = np.array([np.mean(purities[d]) for d in depths])
    stderrs = np.array([
        np.std(purities[d], ddof=1) / np.sqrt(max(len(purities[d]), 1))
        for d in depths
    ])
    stderrs[stderrs == 0] = 1e-9

    # Initial Guess
    B_guess = np.mean(means[-2:]) if len(means) > 1 else means[-1]
    A_guess = means[0] - B_guess
    alpha_guess = 0.99
    p0 = [A_guess, B_guess, alpha_guess]
    bounds = ([-np.inf, 0.0, 0.0], [np.inf, np.inf, 1.0])

    try:
        popt, pcov = curve_fit(
            _prb_decay_model,
            depths,
            means,
            p0=p0,
            sigma=stderrs,
            absolute_sigma=True,
            bounds=bounds,
            maxfev=10000,
            check_finite=True,
        )
        A, B, alpha = popt
        perr = np.sqrt(np.diag(pcov))

        # Calibration: Normalize (P−B)/A
        if abs(A) < 1e-9:
            cal_means, cal_errs = means, stderrs
        else:
            cal_means = (means - B) / A
            cal_errs = stderrs / abs(A)

        return {
            "fit_successful": True,
            "A": float(A),
            "B": float(B),
            "alpha": float(alpha),
            "params": tuple(popt),
            "param_errors": tuple(perr),
            "depths": depths.tolist(),
            "calibrated_mean_purities": cal_means.tolist(),
            "calibrated_std_errors": cal_errs.tolist(),
            "raw_mean_purities": means.tolist(),
        }

    except Exception:
        return _create_prb_failure_result(purities, valid_depths)

# ---------------------------------------------------------------------
# Interleaved Gate‑Error Computation
# ---------------------------------------------------------------------
def calculate_prb_gate_error(
    std_results: PRBFitResult,
    int_results: PRBFitResult,
    num_qubits: int,
) -> GateErrorResult:
    """Compute interleaved‑gate error from standard and interleaved PRB fits."""
    if std_results.get("fit_successful") and int_results.get("fit_successful"):
        alpha_std = std_results["alpha"]
        alpha_int = int_results["alpha"]
        d = 2 ** num_qubits
        if abs(alpha_std) < 1e-9:
            return {"gate_error": np.nan, "calculation_successful": False}
        gate_err = ((d - 1) / d) * (1 - alpha_int / alpha_std)
        return {"gate_error": gate_err, "calculation_successful": True}
    return {"gate_error": np.nan, "calculation_successful": False}

# ---------------------------------------------------------------------
# Failure Constructor
# ---------------------------------------------------------------------
def _create_prb_failure_result(
    purities: Dict[int, List[float]], depths: List[int]
) -> PRBFitResult:
    """Return structured NaN‑filled fallback result."""
    nan3 = (np.nan, np.nan, np.nan)
    raw_means = [np.mean(purities[d]) for d in depths if purities.get(d)]
    raw_stds = [
        np.std(purities[d], ddof=1) / np.sqrt(max(len(purities[d]), 1))
        for d in depths
        if purities.get(d)
    ]
    return {
        "fit_successful": False,
        "A": np.nan,
        "B": np.nan,
        "alpha": np.nan,
        "params": nan3,
        "param_errors": nan3,
        "depths": depths,
        "calibrated_mean_purities": raw_means,
        "calibrated_std_errors": raw_stds,
        "raw_mean_purities": raw_means,
    }

# =============================================================================
# End of File
# =============================================================================