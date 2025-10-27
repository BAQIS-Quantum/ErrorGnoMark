# File Path: errorgnomark/analysis/xeb.py
# [CORRECTED VERSION v2.1 - Updated Plotting Labels]

import logging
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import sem

# Import the SPB functions that will be used
from .spb import analyze_speckle_purity, fit_spb_decay

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Core Analysis Functions ---

def analyze_xeb_fidelity(
    ideal_probabilities: Dict[str, float],
    noisy_counts: Dict[str, int],
    num_qubits: int
) -> float:
    """
    Calculates the normalized linear XEB fidelity for a single circuit run.
    """
    total_shots = sum(noisy_counts.values())
    if total_shots == 0:
        return 0.0

    xeb_sum = 0.0
    for bitstring, count in noisy_counts.items():
        measured_prob = count / total_shots
        ideal_prob = ideal_probabilities.get(bitstring, 0.0)
        xeb_sum += ideal_prob * measured_prob

    d = 2 ** num_qubits
    xeb_raw = d * xeb_sum - 1.0
    fidelity = ((d + 1) / (d - 1)) * xeb_raw

    return max(0.0, min(fidelity, 1.0))

# --- Fitting and Plotting ---

def _exp_decay(x: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """Exponential decay function for fitting: F(m) = A * p^m + B."""
    return A * p**x + B

def fit_xeb_decay(
    x_values: List[int], # Changed name from depths to be more generic
    fidelities_by_x: Dict[int, List[float]],
    num_qubits: int
) -> Dict[str, Any]:
    """
    Fits the normalized XEB fidelity: F(x) = A * p^x + B, with A≈1, B≈0.
    """
    avg_fidelities = np.array([np.mean(fidelities_by_x[x]) for x in x_values], dtype=float)
    initial_guesses = [1.0, 0.999, 0.0] # Adjusted initial guess for p to be closer to expected
    bounds = ([0.0, 0.0, -0.1], [1.5, 1.0, 0.3])

    try:
        params, _ = curve_fit(
            _exp_decay,
            xdata=np.asarray(x_values, dtype=float),
            ydata=avg_fidelities,
            p0=initial_guesses,
            bounds=bounds
        )
    except RuntimeError:
        logging.warning("XEB exponential decay fit failed. Using default parameters.")
        params = initial_guesses

    A_fit, p_fit, B_fit = params
    epc = 1.0 - p_fit

    return {'A': A_fit, 'p': p_fit, 'B': B_fit, 'epc': epc}

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

    x_values = sorted(raw_data.keys())
    avg_fidelities = [np.mean(raw_data[d]) for d in x_values]
    err_fidelities = [sem(raw_data[d]) if len(raw_data[d]) > 1 else 0 for d in x_values]

    ax.errorbar(x_values, avg_fidelities, yerr=err_fidelities, fmt='o', capsize=5, label=plot_kwargs.get('label', 'XEB Fidelity'))

    A, p, B = fit_results['A'], fit_results['p'], fit_results['B']
    epc = fit_results.get('epc', 1.0 - p)
    
    fit_x = np.linspace(min(x_values), max(x_values), 200)
    fit_fidelities = _exp_decay(fit_x, A, p, B)
    
    fit_label = f'Fit: $p={p:.4f}$, EPC$={epc:.5f}$' # Increased precision
    ax.plot(fit_x, fit_fidelities, '--', color=plot_kwargs.get('color', 'C0'), label=fit_label)

    # <<< CHANGE START: Update the x-axis label >>>
    ax.set_xlabel("Noise Exponent (e.g., Native Gate Count)")
    # <<< CHANGE END >>>
    ax.set_ylabel("Fidelity")
    ax.set_title("XEB Fidelity vs. Noise Exponent")
    ax.grid(True, linestyle=':')
    ax.legend()

    if show_plot:
        plt.tight_layout()
        plt.show()

# --- High-Level Orchestrator ---

def analyze_xeb_and_spb_from_results(
    results_by_x: Dict[int, List[Tuple[Dict, Dict]]], # Renamed for clarity
    num_qubits: int
) -> Dict[str, Any]:
    """
    Performs a full XEB and SPB analysis from raw experimental results.
    """
    fidelities_by_x = defaultdict(list)
    purities_by_x = defaultdict(list)
    x_values = sorted(results_by_x.keys())

    for x in x_values:
        results_list = results_by_x[x]
        
        for ideal_probs, noisy_counts in results_list:
            fidelities_by_x[x].append(
                analyze_xeb_fidelity(ideal_probs, noisy_counts, num_qubits)
            )
            purities_by_x[x].append(
                analyze_speckle_purity(ideal_probs, noisy_counts, num_qubits)
            )

    xeb_fit_results = fit_xeb_decay(x_values, fidelities_by_x, num_qubits)
    spb_fit_results = fit_spb_decay(x_values, purities_by_x)

    return {
        'xeb_analysis': {
            'raw_data': fidelities_by_x,
            'fit_results': xeb_fit_results
        },
        'spb_analysis': {
            'raw_data': purities_by_x,
            'fit_results': spb_fit_results
        }
    }