# File Path: errorgnomark/analysis/spb.py
#
# This module provides functions for analyzing and plotting data from
# Speckle Purity Benchmarking (SPB) experiments, adapted to the new framework.

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from typing import Dict, List, Any

def spb_decay_model(m: np.ndarray, A: float, B: float, p: float) -> np.ndarray:
    """The exponential decay model for SPB: Purity(m) = A * p^m + B."""
    return A * p**m + B

def fit_spb_data(purities: Dict[int, List[float]], num_qubits: int) -> Dict[str, Any]:
    """
    Fits SPB data to the exponential decay model and calculates the purity-per-cycle (p_c).
    This version includes a data calibration step to handle SPAM errors and noise robustly.
    """
    depths = np.array(sorted(purities.keys()))
    # For SPB, each "circuit" gives one purity value. We average over circuits of the same depth.
    avg_purities = np.array([np.mean(purities[d]) for d in depths])
    std_devs = np.array([np.std(purities[d]) / np.sqrt(len(purities[d])) for d in depths])

    # --- Data Calibration Step (for robust fitting) ---
    B_guess = avg_purities[-1] if len(avg_purities) > 1 else 0.0
    A_guess = (avg_purities[0] - B_guess) if len(avg_purities) > 0 else 1.0

    if A_guess <= 1e-9: # Handle flat or noisy data
        calibrated_purities = avg_purities
    else:
        calibrated_purities = (avg_purities - B_guess) / A_guess
    
    calibrated_purities = np.clip(calibrated_purities, 0, 1)

    # --- Fitting the Calibrated Data ---
    def calibrated_model(m: np.ndarray, p: float) -> np.ndarray:
        return p**m

    try:
        params, cov = curve_fit(calibrated_model, depths, calibrated_purities, p0=[0.99], bounds=([0.0], [1.0]))
        p_fit = params[0]
        p_fit_err = np.sqrt(np.diag(cov))[0]
        fit_successful = True
    except (RuntimeError, ValueError):
        A_guess, B_guess, p_fit, p_fit_err = 0.0, 0.0, 0.0, 0.0
        fit_successful = False

    # --- Extract Physical Parameters ---
    # For SPB, the fitted decay parameter p_fit is p_c^2.
    p_c = np.sqrt(p_fit) if p_fit >= 0 else 0.0
    p_c_err = p_fit_err / (2 * p_c) if p_c > 1e-9 else 0.0

    return {
        'fit_successful': fit_successful,
        'A': A_guess, 'B': B_guess,
        'p_fit': p_fit, 'p_fit_err': p_fit_err,
        'p_c': p_c, 'p_c_err': p_c_err,
        'depths': depths.tolist(),
        'mean_purities': avg_purities.tolist(),
        'std_devs': std_devs.tolist(),
    }

def calculate_spb_gate_error(results_std: Dict, results_int: Dict, num_qubits: int) -> Dict:
    """Calculates the interleaved gate error from standard and interleaved SPB results."""
    if results_std.get('fit_successful') and results_int.get('fit_successful'):
        p_c_std = results_std['p_c']
        p_c_int = results_int['p_c']
        if p_c_std < 1e-9:
             return {'gate_error': np.nan, 'calculation_successful': False}
        
        p_G = p_c_int / p_c_std
        D = 2**num_qubits
        gate_error = (D - 1) * (1 - p_G) / D
        return {'gate_error': gate_error, 'p_G': p_G, 'calculation_successful': True}
    return {'gate_error': np.nan, 'calculation_successful': False}

def plot_spb_single(results: Dict[str, Any], num_qubits: int):
    """Plots a single SPB decay curve."""
    plt.figure(figsize=(10, 6))
    
    plt.errorbar(results['depths'], results['mean_purities'], yerr=results['std_devs'],
                 fmt='o', color='navy', capsize=5, label='Experimental Data')
    
    if results['fit_successful']:
        p_c, p_c_err = results['p_c'], results['p_c_err']
        fine_depths = np.linspace(0, max(results['depths']), 200)
        fit_curve = spb_decay_model(fine_depths, results['A'], results['B'], results['p_fit'])
        label = f'Fit ($p_c = {p_c:.4f} \pm {p_c_err:.1e}$)'
        plt.plot(fine_depths, fit_curve, 'r-', linewidth=2, label=label)

    plt.xlabel("Clifford Sequence Depth (m)", fontsize=12)
    plt.ylabel("Measured Purity", fontsize=12)
    plt.title(f"Standard {num_qubits}-Qubit Speckle Purity Benchmarking", fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()

def plot_spb_comparison(results_std: Dict, results_int: Dict, num_qubits: int, target_gate_name: str):
    """Plots both standard and interleaved SPB decay curves."""
    plt.figure(figsize=(10, 6))
    
    # Plot Standard Data
    p_c_std = results_std.get('p_c', 0)
    plt.errorbar(results_std['depths'], results_std['mean_purities'], yerr=results_std['std_devs'],
                 fmt='o', color='blue', capsize=5, label=f'Standard Data ($p_c={p_c_std:.4f}$)')
    if results_std['fit_successful']:
        fine_depths = np.linspace(0, max(results_std['depths']), 200)
        fit_curve = spb_decay_model(fine_depths, results_std['A'], results_std['B'], results_std['p_fit'])
        plt.plot(fine_depths, fit_curve, color='blue', linestyle='--')

    # Plot Interleaved Data
    p_c_int = results_int.get('p_c', 0)
    plt.errorbar(results_int['depths'], results_int['mean_purities'], yerr=results_int['std_devs'],
                 fmt='s', color='red', capsize=5, label=f'Interleaved Data ($p_c={p_c_int:.4f}$)')
    if results_int['fit_successful']:
        fine_depths = np.linspace(0, max(results_int['depths']), 200)
        fit_curve = spb_decay_model(fine_depths, results_int['A'], results_int['B'], results_int['p_fit'])
        plt.plot(fine_depths, fit_curve, color='red', linestyle='--')

    plt.xlabel("Clifford Sequence Depth (m)", fontsize=12)
    plt.ylabel("Measured Purity", fontsize=12)
    plt.title(f"Interleaved SPB for '{target_gate_name}' on {num_qubits} Qubit(s)", fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()