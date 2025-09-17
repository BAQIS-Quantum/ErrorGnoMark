# File Path: errorgnomark/analysis/benchmarking/rb_analysis.py
# RESTRUCTURED for Standard and Interleaved RB analysis.

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from typing import Dict, List, Optional

def rb_decay_model(m: np.ndarray, A: float, B: float, p: float) -> np.ndarray:
    """The exponential decay model for Randomized Benchmarking: F(m) = A * p^m + B."""
    return A * p**m + B

def fit_rb_data(survivals: Dict[int, List[float]], num_qubits: int) -> Dict:
    """
    Fits RB survival probability data to the exponential decay model and calculates EPC.
    This is the core fitting engine for BOTH standard and interleaved RB.

    Args:
        survivals: A dictionary mapping sequence depth (m) to a list of survival probabilities.
        num_qubits: The number of qubits in the RB experiment.

    Returns:
        A dictionary containing the fit results, including the Error Per Clifford (EPC).
    """
    depths = np.array(sorted(survivals.keys()))
    avg_survivals = np.array([np.mean(survivals[d]) for d in depths])
    
    d = 2**num_qubits
    initial_guess = [1 - 1/d, 1/d, 0.99]
    bounds = ([0, 0, 0], [1, 1, 1])

    try:
        params, _ = curve_fit(
            rb_decay_model, depths, avg_survivals, p0=initial_guess, bounds=bounds, maxfev=5000
        )
        A, B, p = params
        
        # --- [MODIFIED AS PER YOUR REQUEST] ---
        # The primary result of a fit is the Error Per Clifford (EPC).
        epc = (d - 1) * (1 - p) / d
        # --- [END MODIFICATION] ---

        fit_successful = True
    except RuntimeError:
        A, B, p, epc = 0, 0, 0, 1.0
        fit_successful = False

    return {
        'fit_successful': fit_successful,
        'A': A, 'B': B, 'p': p,
        'epc': epc, # Error Per Clifford
        'depths': depths.tolist(),
        'mean_survivals': avg_survivals.tolist()
    }

def plot_rb_comparison(
    results_std: Dict,
    results_int: Dict,
    num_qubits: int,
    target_gate_name: str,
    save_path: Optional[str] = None
):
    """Plots both standard and interleaved decay curves on the same axes."""
    plt.figure(figsize=(10, 7))
    
    # Plot Standard RB data and fit
    plt.errorbar(
        results_std['depths'], results_std['mean_survivals'],
        fmt='o', color='navy', capsize=5, label=f'Standard RB (EPC={results_std["epc"]:.2e})'
    )
    if results_std['fit_successful']:
        fine_depths = np.linspace(0, max(results_std['depths']), 200)
        fit_curve = rb_decay_model(fine_depths, results_std['A'], results_std['B'], results_std['p'])
        plt.plot(fine_depths, fit_curve, color='cornflowerblue', linestyle='--')

    # Plot Interleaved RB data and fit
    plt.errorbar(
        results_int['depths'], results_int['mean_survivals'],
        fmt='s', color='darkred', capsize=5, label=f'Interleaved RB ({target_gate_name}) (EPC={results_int["epc"]:.2e})'
    )
    if results_int['fit_successful']:
        fine_depths = np.linspace(0, max(results_int['depths']), 200)
        fit_curve = rb_decay_model(fine_depths, results_int['A'], results_int['B'], results_int['p'])
        plt.plot(fine_depths, fit_curve, color='lightcoral', linestyle='--')

    plt.xlabel("Clifford Sequence Depth (m)", fontsize=12)
    plt.ylabel("Survival Probability", fontsize=12)
    plt.title(f"Interleaved RB for '{target_gate_name}' on {num_qubits} Qubit(s)", fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.show(block=True)
    plt.close()

def plot_rb_single(results: Dict, num_qubits: int, save_path: Optional[str] = None):
    """Plots a single RB decay curve (used for Standard RB)."""
    plt.figure(figsize=(10, 7))
    
    plt.errorbar(
        results['depths'], results['mean_survivals'],
        fmt='o', color='navy', capsize=5, label=f'Data (Avg)'
    )
    if results['fit_successful']:
        epc = results['epc']
        fine_depths = np.linspace(0, max(results['depths']), 200)
        fit_curve = rb_decay_model(fine_depths, results['A'], results['B'], results['p'])
        plt.plot(fine_depths, fit_curve, 'r-', linewidth=2, label=f'Fit (EPC = {epc:.2e})')

    plt.xlabel("Clifford Sequence Depth (m)", fontsize=12)
    plt.ylabel("Survival Probability", fontsize=12)
    plt.title(f"Standard {num_qubits}-Qubit Randomized Benchmarking", fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.show(block=True)
    plt.close()