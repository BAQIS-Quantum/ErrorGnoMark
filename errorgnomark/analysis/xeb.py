# File Path: errorgnomark/analysis/benchmarking/xeb_analysis.py
# [CORRECTED VERSION]

from collections import defaultdict
from typing import Dict, List, Tuple, Union

import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# =========================================================================
# --- Core Analysis Functions ---
# =========================================================================

def analyze_xeb_fidelity(
    ideal_probabilities: Dict[str, float], 
    noisy_counts: Dict[str, int]
) -> float:
    """
    Calculates the linear cross-entropy fidelity using the full ideal probability distribution.

    Args:
        ideal_probabilities: A dictionary mapping bitstrings to their ideal probabilities.
        noisy_counts: A dictionary mapping bitstrings to their measured counts from a noisy backend.

    Returns:
        The linear XEB fidelity, a float value.
    """
    total_shots = sum(noisy_counts.values())
    if total_shots == 0:
        return 0.0

    if not ideal_probabilities:
        # Get num_qubits from noisy_counts if ideal is empty
        if not noisy_counts: return 0.0
        num_qubits = len(next(iter(noisy_counts.keys())))
    else:
        num_qubits = len(next(iter(ideal_probabilities.keys())))
    
    dimension = 2**num_qubits

    # [THE FIX] This is the correct Linear XEB formula: D * <P_ideal>_noisy - 1
    # where <P_ideal>_noisy is the expectation value of the ideal distribution
    # over the noisy measurements.
    expected_value = 0.0
    for bitstring, count in noisy_counts.items():
        # Get the ideal probability for the measured bitstring
        ideal_prob = ideal_probabilities.get(bitstring, 0.0)
        # Add its contribution to the total expectation value
        expected_value += (count / total_shots) * ideal_prob

    linear_fidelity = dimension * expected_value - 1.0
    return float(linear_fidelity)


def fit_xeb_fidelity_decay(fidelities_by_depth: Dict[int, List[float]]) -> Dict:
    """
    Fits XEB fidelity data to an exponential decay model F(d) = A * p^d.
    """
    depths = sorted(fidelities_by_depth.keys())
    # [FIX] Filter out non-physical fidelities before averaging
    mean_fidelities = []
    std_fidelities = []
    for d in depths:
        valid_fidelities = [f for f in fidelities_by_depth[d] if -1.5 <= f <= 1.5]
        if not valid_fidelities: valid_fidelities = [0.0] # Avoid empty list errors
        mean_fidelities.append(np.mean(valid_fidelities))
        std_fidelities.append(np.std(valid_fidelities))

    mean_fidelities = np.array(mean_fidelities)
    std_fidelities = np.array(std_fidelities)

    def decay_model(d, A, p):
        return A * (p**d)

    initial_guess = [1.0, 0.99]
    bounds = ([0, 0], [1.5, 1.0]) 

    try:
        params, covariance = curve_fit(
            decay_model,
            np.array(depths),
            mean_fidelities,
            p0=initial_guess,
            sigma=std_fidelities if np.any(std_fidelities > 0) else None,
            bounds=bounds,
            maxfev=5000
        )
        A, p = params
        error_per_cycle = 1.0 - p
    except (RuntimeError, ValueError):
        A, p, error_per_cycle = np.nan, np.nan, np.nan
        params, covariance = [A, p], np.full((2, 2), np.nan)

    return {
        'A': A,
        'p': p,
        'error_per_cycle': error_per_cycle,
        'fit_params': params,
        'fit_covariance': covariance,
    }

def calculate_interleaved_xeb_error(p_std: float, p_int: float, num_qubits: int) -> Dict:
    """
    Calculates the error of an interleaved gate from standard and interleaved decay rates.
    """
    dimension = 2**num_qubits
    
    # Fidelity of the target gate is the ratio of the decay parameters
    gate_fidelity = p_int / p_std if p_std != 0 else 0
    
    # Convert fidelity to error using the standard formula
    gate_error = (dimension - 1) / dimension * (1 - gate_fidelity)

    return {
        'gate_fidelity': gate_fidelity,
        'error_per_gate': gate_error
    }

# =========================================================================
# --- Plotting Functions ---
# =========================================================================

def plot_xeb_decay(
    fidelities_by_depth: Dict[int, List[float]],
    fit_results: Dict,
    ax: plt.Axes,
    label: str,
    color: str
):
    """
    Plots XEB fidelity decay data and its exponential fit on a given axis.
    """
    depths = sorted(fidelities_by_depth.keys())
    mean_fidelities = np.array([np.mean(fidelities_by_depth[d]) for d in depths])
    # Calculate standard error of the mean for error bars
    sem_fidelities = np.array([np.std(fidelities_by_depth[d]) / np.sqrt(len(fidelities_by_depth[d])) for d in depths])
    
    ax.errorbar(
        depths,
        mean_fidelities,
        yerr=sem_fidelities,
        fmt='o',
        capsize=4,
        label=f'{label} Data',
        color=color
    )

    A = fit_results['A']
    p = fit_results['p']
    error_per_cycle = fit_results['error_per_cycle']
    
    fit_depths = np.linspace(min(depths), max(depths), 200)
    fit_fidelities = A * (p**fit_depths)
    
    plot_label = f'{label} Fit\nEPC = {error_per_cycle:.2e}'
    ax.plot(fit_depths, fit_fidelities, linestyle='--', color=color, label=plot_label)