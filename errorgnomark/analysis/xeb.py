# File Path: errorgnomark/analysis/xeb.py
# [DEFINITIVE FINAL VERSION - Corrected UnboundLocalError in plot_xeb_decay]

import logging
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import sem

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Core Analysis Functions ---

def analyze_xeb_fidelity(
    ideal_probabilities: Dict[str, float],
    noisy_counts: Dict[str, int],
    num_qubits: int
) -> float:
    """
    Calculates the linear cross-entropy fidelity for a single circuit run.
    """
    total_shots = sum(noisy_counts.values())
    if total_shots == 0:
        return 0.0

    xeb_sum = 0.0
    for bitstring, count in noisy_counts.items():
        measured_prob = count / total_shots
        ideal_prob = ideal_probabilities.get(bitstring, 0.0)
        xeb_sum += ideal_prob * measured_prob

    d = 2**num_qubits
    fidelity = (d * xeb_sum - 1) / (d - 1)
    
    return max(0.0, min(fidelity, 1.0))

# --- Fitting and Plotting ---

def _exp_decay(x: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """Exponential decay function for fitting: F(m) = A * p^m + B."""
    return A * p**x + B

def fit_xeb_decay(
    depths: List[int],
    fidelities_by_depth: Dict[int, List[float]],
    num_qubits: int
) -> Dict[str, Any]:
    """
    Fits the XEB fidelity decay to an exponential model and calculates EPC.
    """
    avg_fidelities = np.array([np.mean(fidelities_by_depth[d]) for d in depths])
    
    d = 2**num_qubits
    initial_guesses = [1.0 - 1/d, 0.98, 1/d]

    try:
        params, _ = curve_fit(
            _exp_decay,
            xdata=depths,
            ydata=avg_fidelities,
            p0=initial_guesses,
            bounds=([0, 0, 0], [1.5, 1.0, 1.0])
        )
    except RuntimeError:
        logging.warning("Exponential decay fit failed. Using default parameters.")
        params = initial_guesses

    A_fit, p_fit, B_fit = params
    epc = 1.0 - p_fit

    return {
        'A': A_fit,
        'p': p_fit,
        'B': B_fit,
        'epc': epc
    }

def plot_xeb_decay(
    raw_data: Dict[int, List[float]],
    fit_results: Dict[str, float],
    ax: Optional[plt.Axes] = None,
    **plot_kwargs
) -> None:
    """Plots the XEB fidelity decay and the exponential fit."""
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        show_plot = True
    else:
        show_plot = False

    depths = sorted(raw_data.keys())
    avg_fidelities = [np.mean(raw_data[d]) for d in depths]
    err_fidelities = [sem(raw_data[d]) if len(raw_data[d]) > 1 else 0 for d in depths]

    ax.errorbar(depths, avg_fidelities, yerr=err_fidelities, fmt='o', capsize=5, label=plot_kwargs.get('label', 'XEB Fidelity'))

    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    # [[[ FIX: Separated assignment to prevent UnboundLocalError ]]]
    # First, unpack the guaranteed values from the fit.
    A, p, B = fit_results['A'], fit_results['p'], fit_results['B']
    # Then, safely get 'epc', using the now-defined 'p' to calculate the default.
    epc = fit_results.get('epc', 1.0 - p)
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    fit_depths = np.linspace(min(depths), max(depths), 200)
    fit_fidelities = _exp_decay(fit_depths, A, p, B)
    
    fit_label = f'Fit: $p={p:.3f}$, EPC$={epc:.4f}$'
    ax.plot(fit_depths, fit_fidelities, '--', color=plot_kwargs.get('color', 'C0'), label=fit_label)

    ax.set_xlabel("Circuit Depth (m)")
    ax.set_ylabel("Fidelity")
    ax.set_title("XEB Fidelity vs. Circuit Depth")
    ax.grid(True, linestyle=':')
    ax.legend()

    if show_plot:
        plt.tight_layout()
        plt.show()

# --- High-Level Orchestrator ---

def analyze_xeb_and_spb_from_results(
    results_by_depth: Dict[int, List[Tuple[Dict, Dict]]],
    num_qubits: int
) -> Dict[str, Any]:
    """
    Performs a full XEB and SPB analysis from raw experimental results.
    """
    from .spb import analyze_speckle_purity, fit_spb_decay

    fidelities_by_depth = defaultdict(list)
    purities_by_depth = defaultdict(list)
    depths = sorted(results_by_depth.keys())

    for depth in depths:
        results_list = results_by_depth[depth]
        for ideal_probs, noisy_counts in results_list:
            fidelities_by_depth[depth].append(analyze_xeb_fidelity(ideal_probs, noisy_counts, num_qubits))
        
        purity, _ = analyze_speckle_purity(results_list, num_qubits)
        purities_by_depth[depth] = purity

    xeb_fit_results = fit_xeb_decay(depths, fidelities_by_depth, num_qubits)
    spb_fit_results = fit_spb_decay(depths, purities_by_depth)

    return {
        'xeb_analysis': {
            'raw_data': fidelities_by_depth,
            'fit_results': xeb_fit_results
        },
        'spb_analysis': {
            'raw_data': purities_by_depth,
            'fit_results': spb_fit_results
        }
    }