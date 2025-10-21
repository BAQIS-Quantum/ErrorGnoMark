# File Path: errorgnomark/analysis/spb.py
#
# [DEFINITIVE FINAL VERSION - Corrected Per-Circuit Purity Calculation]

import logging
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import sem

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Core Analysis Function ---

def analyze_speckle_purity(
    ideal_probabilities: Dict[str, float],
    noisy_counts: Dict[str, int],
    num_qubits: int
) -> float:
    """
    Calculates the speckle purity for a SINGLE circuit run.

    This per-circuit method correctly assesses the "spikiness" or "speckle" of
    an individual outcome distribution. The purity for a single circuit is calculated
    based on the variance of its measured probability distribution, as per Google's
    2019 paper (Eq. 49), which provides a direct estimator for p^2.

    Args:
        ideal_probabilities: Ideal probabilities for a single circuit. (Not used in this
                             purity estimation method, but kept for consistent function signature).
        noisy_counts: The noisy measurement counts for that single circuit.
        num_qubits: The number of qubits in the circuit.

    Returns:
        A single float value representing the speckle purity (p^2) for this circuit.
    """
    total_shots = sum(noisy_counts.values())
    if total_shots == 0:
        return 0.0

    d = 2**num_qubits
    if d <= 1:
        return 0.0 # Avoid division by zero for single qubit or invalid cases

    # This scaling factor comes from the relationship between purity and the variance
    # of the measured probability distribution under a depolarizing noise model.
    # p^2 = [d^2 * (d+1) / (d-1)] * Var(P_exp)
    scaling_factor = (d**2 * (d + 1)) / (d - 1)

    # Step 1: Create the full experimental probability vector P_exp of size d.
    # It's crucial that this vector has size d = 2**n to correctly calculate variance.
    p_exp = np.zeros(d)
    for bitstring, count in noisy_counts.items():
        index = int(bitstring, 2)
        if index < d:
            p_exp[index] = count / total_shots
    
    # Step 2: Calculate the variance of THIS circuit's probability distribution.
    var_p_exp = np.var(p_exp)

    # Step 3: Apply Google's formula to get the purity (p^2) for this circuit.
    purity_p_squared = var_p_exp * scaling_factor
    
    # Clamp to handle statistical fluctuations that might push the value
    # slightly below 0 or unnaturally high.
    purity_p_squared = max(0.0, min(purity_p_squared, 1.5)) # Allow slightly > 1 for noise
    
    return purity_p_squared


# --- Fitting and Plotting Functions ---

def _exp_decay_spb(x: np.ndarray, C: float, p_sq: float, D: float) -> np.ndarray:
    """Exponential decay function for SPB fitting: P(m) = C * (p_sq)^m + D."""
    return C * (p_sq**x) + D

def fit_spb_decay(
    depths: List[int],
    purities_by_depth: Dict[int, List[float]]
) -> Dict[str, Any]:
    """
    Fits the speckle purity decay to an exponential model.
    This version is updated to handle a list of purities for each depth.
    """
    depth_keys = sorted(purities_by_depth.keys())
    # Calculate the average purity for each depth from the list of purities.
    avg_purities = np.array([np.mean(purities_by_depth[d]) for d in depth_keys])

    # Initial guesses for the fit parameters [C, p_sq, D]
    initial_guesses = [1.0, 0.95, 0.0]

    try:
        # Physical bounds: C should be around 1, p_sq between 0 and 1, D around 0.
        params, _ = curve_fit(
            _exp_decay_spb,
            xdata=depth_keys,
            ydata=avg_purities,
            p0=initial_guesses,
            bounds=([0, 0, -0.1], [1.5, 1.0, 0.1]) 
        )
    except RuntimeError:
        logging.warning("SPB exponential decay fit failed. Using default parameters.")
        params = initial_guesses

    C_fit, p_sq_fit, D_fit = params

    fit_results = {
        'C': C_fit,
        'p_sq': p_sq_fit,
        'D': D_fit,
    }
    return fit_results

def plot_spb_decay(
    raw_data: Dict[int, List[float]],
    fit_results: Dict[str, float],
    ax: Optional[plt.Axes] = None,
    **plot_kwargs
) -> None:
    """
    Plots the speckle purity decay and the exponential fit.
    This version includes error bars based on the distribution of purities at each depth.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        show_plot = True
    else:
        show_plot = False

    depths = sorted(raw_data.keys())
    avg_purities = [np.mean(raw_data[d]) for d in depths]
    # Calculate standard error of the mean for the purities at each depth for error bars.
    err_purities = [sem(raw_data[d]) if len(raw_data[d]) > 1 else 0 for d in depths]

    # Plot data points with error bars
    ax.errorbar(depths, avg_purities, yerr=err_purities, fmt='o', capsize=5, label=plot_kwargs.get('label', 'Speckle Purity ($p^2$)'))

    # Plot the fit curve
    C, p_sq, D = fit_results['C'], fit_results['p_sq'], fit_results['D']
    
    fit_depths = np.linspace(min(depths), max(depths), 200)
    fit_purities = _exp_decay_spb(fit_depths, C, p_sq, D)
    
    fit_label = f'Fit: $p^2_{{cycle}}={p_sq:.3f}$'
    ax.plot(fit_depths, fit_purities, '--', color=plot_kwargs.get('color', 'C1'), label=fit_label)

    ax.set_xlabel("Circuit Depth (m)")
    ax.set_ylabel("Speckle Purity ($p^2$)")
    ax.set_title("Speckle Purity vs. Circuit Depth")
    ax.grid(True, linestyle=':')
    ax.legend()
    ax.set_ylim(bottom=-0.1, top=1.1)

    if show_plot:
        plt.tight_layout()
        plt.show()