# File Path: errorgnomark/analysis/spb.py
#
# [DEFINITIVE FINAL VERSION v3 - Complete Implementation]

import logging
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import sem

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Core Analysis Function ---

def analyze_speckle_purity(
    results_list: List[Tuple[Dict[str, float], Dict[str, int]]],
    num_qubits: int
) -> Tuple[float, float]:
    """
    Calculates the speckle purity and its standard error for a set of circuits at a single depth.

    Args:
        results_list: A list of (ideal_probabilities, noisy_counts) tuples for a single depth.
        num_qubits: The number of qubits in the circuits.

    Returns:
        A tuple containing the average speckle purity and its standard error.
    """
    if not results_list:
        return 0.0, 0.0

    d = 2**num_qubits
    purities = []

    for ideal_probs, noisy_counts in results_list:
        total_shots = sum(noisy_counts.values())
        if total_shots == 0:
            continue

        # Calculate the linear XEB sum for this circuit
        xeb_sum = 0.0
        for bitstring, count in noisy_counts.items():
            measured_prob = count / total_shots
            ideal_prob = ideal_probs.get(bitstring, 0.0)
            xeb_sum += ideal_prob * measured_prob
        
        # Calculate the purity for this single circuit
        purity = (d * xeb_sum - 1) / (d - 1)
        purities.append(purity)
    
    if not purities:
        return 0.0, 0.0

    avg_purity = np.mean(purities)
    std_err = sem(purities) if len(purities) > 1 else 0.0

    return avg_purity, std_err

# --- Fitting and Plotting Functions ---

def _exp_decay_spb(x: np.ndarray, C: float, p_sq: float, D: float) -> np.ndarray:
    """Exponential decay function for SPB fitting: P(m) = C * (p_sq)^m + D."""
    return C * (p_sq**x) + D

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# [[[ THIS IS THE FUNCTION THAT WAS MISSING FROM THE FILE ]]]
def fit_spb_decay(
    depths: List[int],
    purities_by_depth: Dict[int, float]
) -> Dict[str, Any]:
    """
    Fits the speckle purity decay to an exponential model.
    """
    depth_keys = sorted(purities_by_depth.keys())
    avg_purities = np.array([purities_by_depth[d] for d in depth_keys])

    # Initial guesses for the fit parameters [C, p_sq, D]
    D_guess = 0.0  # Asymptotic value for SPB is 0
    C_guess = 1.0
    p_sq_guess = 0.95 # A reasonable starting guess for squared fidelity per cycle
    initial_guesses = [C_guess, p_sq_guess, D_guess]

    try:
        params, _ = curve_fit(
            _exp_decay_spb,
            xdata=depth_keys,
            ydata=avg_purities,
            p0=initial_guesses,
            bounds=([0, 0, -0.1], [1.5, 1.0, 0.1]) # Physical bounds
        )
    except RuntimeError:
        logging.warning("SPB exponential decay fit failed. Using default parameters.")
        params = [C_guess, p_sq_guess, D_guess]

    C_fit, p_sq_fit, D_fit = params

    fit_results = {
        'C': C_fit,
        'p_sq': p_sq_fit,
        'D': D_fit,
    }
    return fit_results
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def plot_spb_decay(
    raw_data: Dict[int, float],
    fit_results: Dict[str, float],
    ax: Optional[plt.Axes] = None,
    **plot_kwargs
) -> None:
    """Plots the speckle purity decay and the exponential fit."""
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        show_plot = True
    else:
        show_plot = False

    depths = sorted(raw_data.keys())
    avg_purities = [raw_data[d] for d in depths]

    # Plot individual data points
    ax.plot(depths, avg_purities, 'o', label=plot_kwargs.get('label', 'Speckle Purity'))

    # Plot the fit curve
    C, p_sq, D = fit_results['C'], fit_results['p_sq'], fit_results['D']
    
    fit_depths = np.linspace(min(depths), max(depths), 200)
    fit_purities = _exp_decay_spb(fit_depths, C, p_sq, D)
    
    fit_label = f'Fit: $p^2={p_sq:.3f}$'
    ax.plot(fit_depths, fit_purities, '--', color=plot_kwargs.get('color', 'C1'), label=fit_label)

    ax.set_xlabel("Circuit Depth (m)")
    ax.set_ylabel("Speckle Purity")
    ax.set_title("Speckle Purity vs. Circuit Depth")
    ax.grid(True, linestyle=':')
    ax.legend()

    if show_plot:
        plt.tight_layout()
        plt.show()