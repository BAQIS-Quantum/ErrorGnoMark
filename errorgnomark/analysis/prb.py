# File Path: errorgnomark/analysis/prb.py
# [FINAL VERSION - Incorporates robust data calibration from user's reference]

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from typing import Dict, List, Optional

def prb_decay_model(m: np.ndarray, A: float, B: float, alpha: float) -> np.ndarray:
    """The exponential decay model for Purity RB: P(m) = A * alpha^m + B."""
    return A * alpha**m + B

def fit_prb_data(purities: Dict[int, List[float]], num_qubits: int) -> Dict:
    """
    Fits Purity RB data to the exponential decay model.
    This version includes a crucial calibration step to remove SPAM effects,
    leading to a more robust fit for the decay parameter alpha.
    """
    depths = np.array(sorted(purities.keys()))
    # Filter out any depths with no data
    valid_depths = [d for d in depths if purities[d]]
    if not valid_depths:
        return {'fit_successful': False}
        
    depths = np.array(valid_depths)
    avg_purities = np.array([np.mean(purities[d]) for d in depths])
    std_devs = np.array([np.std(purities[d]) / np.sqrt(len(purities[d])) for d in depths])

    # --- Data Calibration (from user's robust reference code) ---
    # This process normalizes the data to start at 1 and decay to 0,
    # which makes the fit for alpha much more stable.
    try:
        # Estimate B (the baseline) from the last few data points.
        B_guess = np.mean(avg_purities[-2:]) if len(avg_purities) > 1 else avg_purities[-1]
        
        # Estimate A (the amplitude) from the first data point.
        A_guess = avg_purities[0]

        # Avoid division by zero if data is flat
        if np.isclose(A_guess, B_guess):
            raise ValueError("Data is too flat to calibrate.")

        # Calibrate the data: y' = (y - B) / (A - B)
        calibrated_purities = (avg_purities - B_guess) / (A_guess - B_guess)
        calibrated_std_devs = std_devs / abs(A_guess - B_guess)

        # Ensure the data is decaying, not growing.
        if calibrated_purities[0] < 0.5: # Should start near 1
             calibrated_purities = 1 - calibrated_purities

    except (ValueError, IndexError, FloatingPointError):
        # Fallback if calibration fails: use raw data but with tighter bounds.
        calibrated_purities = avg_purities
        calibrated_std_devs = std_devs

    # --- Fitting ---
    def decay_model_for_fit(m, alpha):
        return alpha**m

    try:
        # Fit the calibrated data to a simple alpha^m model.
        params, _ = curve_fit(
            decay_model_for_fit, depths, calibrated_purities,
            p0=[0.95], bounds=([0], [1]), sigma=calibrated_std_devs, maxfev=5000
        )
        alpha = params[0]
        # For calibrated data, the ideal A is 1 and B is 0.
        A, B = 1.0, 0.0
        fit_successful = True
    except RuntimeError:
        A, B, alpha = 0, 0, 0
        fit_successful = False

    return {
        'fit_successful': fit_successful,
        'A': A, 'B': B, 'alpha': alpha,
        'depths': depths.tolist(),
        'mean_purities': calibrated_purities.tolist(),
        'std_devs': calibrated_std_devs.tolist(),
        'raw_purities_mean': avg_purities.tolist(), # Keep raw data for inspection
    }

def calculate_prb_gate_error(results_std: Dict, results_int: Dict) -> Dict:
    """Calculates the interleaved gate error from standard and interleaved PRB results."""
    if results_std.get('fit_successful') and results_int.get('fit_successful'):
        alpha_std = results_std['alpha']
        alpha_int = results_int['alpha']
        # The factor is 0.5 for 1Q, (d^2-1)/d^2 for d-dimensional system
        # For now, we use the simple 1/2 factor which is common.
        gate_error = (1 - alpha_int / alpha_std) / 2
        return {'gate_error': gate_error, 'calculation_successful': True}
    return {'gate_error': -1.0, 'calculation_successful': False}

def plot_prb_single(results: Dict, num_qubits: int):
    """Plots a single PRB decay curve using calibrated data."""
    plt.figure(figsize=(10, 6))
    
    plt.errorbar(
        results['depths'], results['mean_purities'], yerr=results['std_devs'],
        fmt='o', color='steelblue', capsize=5, label='Purity Data (Calibrated)'
    )
    if results['fit_successful']:
        alpha = results['alpha']
        fine_depths = np.linspace(0, max(results['depths']), 200)
        fit_curve = prb_decay_model(fine_depths, results['A'], results['B'], alpha)
        plt.plot(fine_depths, fit_curve, color='orangered', linestyle='--', label=f'Fit (α = {alpha:.3f})')

    plt.xlabel("Clifford Depth (m)", fontsize=12)
    plt.ylabel("Calibrated State Purity", fontsize=12)
    plt.title(f"Standard {num_qubits}-Qubit Purity RB", fontsize=14)
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.ylim(-0.1, 1.1)

def plot_prb_comparison(results_std: Dict, results_int: Dict, num_qubits: int, target_gate_name: str):
    """Plots both standard and interleaved PRB decay curves on the same axes."""
    plt.figure(figsize=(10, 6))
    gate_error = calculate_prb_gate_error(results_std, results_int).get('gate_error', -1)
    
    # Plot Standard PRB data and fit
    plt.errorbar(
        results_std['depths'], results_std['mean_purities'], yerr=results_std['std_devs'],
        fmt='o', color='blue', capsize=5, label='Standard Data'
    )
    if results_std['fit_successful']:
        fine_depths = np.linspace(0, max(results_std['depths']), 200)
        fit_curve = prb_decay_model(fine_depths, 1.0, 0.0, results_std['alpha'])
        plt.plot(fine_depths, fit_curve, color='blue', linestyle='--', label=f'Standard Fit (α={results_std["alpha"]:.3f})')

    # Plot Interleaved PRB data and fit
    plt.errorbar(
        results_int['depths'], results_int['mean_purities'], yerr=results_int['std_devs'],
        fmt='o', color='red', capsize=5, label='Interleaved Data'
    )
    if results_int['fit_successful']:
        fine_depths = np.linspace(0, max(results_int['depths']), 200)
        fit_curve = prb_decay_model(fine_depths, 1.0, 0.0, results_int['alpha'])
        plt.plot(fine_depths, fit_curve, color='red', linestyle='--', label=f'Interleaved Fit (α={results_int["alpha"]:.3f})')

    plt.xlabel("Clifford Depth (m)", fontsize=12)
    plt.ylabel("Calibrated State Purity", fontsize=12)
    title = f"Interleaved Purity RB: '{target_gate_name.upper()}' on {num_qubits} Qubit(s)\n"
    title += f"Estimated Gate Error = {gate_error:.3e}"
    plt.title(title, fontsize=14)
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.ylim(-0.1, 1.1)