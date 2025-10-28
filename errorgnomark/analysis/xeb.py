# File Path: errorgnomark/analysis/xeb.py
# [CORRECTED VERSION v2.1 - Updated Plotting Labels]
# Description: This file contains the core functions for performing Cross-Entropy Benchmarking (XEB)
# and Speckle Purity Benchmarking (SPB) analysis. Its primary responsibilities include calculating
# fidelity for single runs, fitting fidelity decay curves against a noise parameter (like circuit depth),
# visualizing the results, and orchestrating the end-to-end analysis workflow.

import logging
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

# Import scientific computing and plotting libraries
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit  # Used for curve fitting
from scipy.stats import sem           # Used for calculating the standard error of the mean

# Import the SPB functions that will be used from the sibling spb.py module
from .spb import analyze_speckle_purity, fit_spb_decay

# Configure a basic logger to output informational, warning, or error messages during execution
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Core Analysis Functions ---

def analyze_xeb_fidelity(
    ideal_probabilities: Dict[str, float],
    noisy_counts: Dict[str, int],
    num_qubits: int
) -> float:
    """
    Calculates the normalized linear XEB fidelity for a single circuit run.

    This fidelity measures how much more likely the measured outcomes are under the
    ideal probability distribution compared to the uniform distribution.

    Args:
        ideal_probabilities (Dict[str, float]): A dictionary mapping ideal output bitstrings
                                                 to their theoretical probabilities.
        noisy_counts (Dict[str, int]): A dictionary mapping measured bitstrings to their
                                       observed counts (shots).
        num_qubits (int): The number of qubits in the circuit.

    Returns:
        float: The calculated linear XEB fidelity, clamped between 0.0 and 1.0.
    """
    # Calculate the total number of measurement shots
    total_shots = sum(noisy_counts.values())
    # If there were no shots, fidelity is zero.
    if total_shots == 0:
        return 0.0

    # This loop calculates the core of XEB: sum(P_ideal(i) * P_measured(i))
    # It represents the overlap between the ideal and measured distributions.
    xeb_sum = 0.0
    for bitstring, count in noisy_counts.items():
        measured_prob = count / total_shots
        ideal_prob = ideal_probabilities.get(bitstring, 0.0) # Look up the ideal probability
        xeb_sum += ideal_prob * measured_prob

    # The Hilbert space dimension 'd' is 2^N for N qubits.
    d = 2 ** num_qubits
    # The raw XEB value is scaled by 'd' and shifted. A value of 0 corresponds
    # to the uniform distribution, while 1 corresponds to a perfect match.
    xeb_raw = d * xeb_sum - 1.0
    
    # Normalize the raw value to get the final fidelity. This mapping ensures that
    # the fidelity is a more direct estimator of the true quantum state fidelity.
    fidelity = ((d + 1) / (d - 1)) * xeb_raw

    # Clamp the result to the valid range [0, 1] to handle potential floating-point
    # inaccuracies or statistical fluctuations that might push it slightly out of bounds.
    return max(0.0, min(fidelity, 1.0))

# --- Fitting and Plotting ---

def _exp_decay(x: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """
    Exponential decay function for fitting: F(m) = A * p^m + B.
    This model is used to describe how fidelity (F) decays as a function of
    a noise-proportional parameter 'x' (e.g., circuit depth or cycle number 'm').
    - A: Amplitude (ideally close to 1)
    - p: Depolarizing parameter (related to fidelity per cycle)
    - B: Offset (ideally close to 0)
    """
    return A * p**x + B

def fit_xeb_decay(
    x_values: List[int], # Changed name from 'depths' to be more generic
    fidelities_by_x: Dict[int, List[float]],
    num_qubits: int # num_qubits is not directly used here but kept for API consistency
) -> Dict[str, Any]:
    """
    Fits the average XEB fidelity to the exponential decay model: F(x) = A * p^x + B.
    From the fit, it extracts the depolarizing parameter 'p' and calculates the
    Error Per Cycle (EPC).

    Args:
        x_values (List[int]): The list of independent variable values (e.g., circuit depths).
        fidelities_by_x (Dict[int, List[float]]): A dictionary mapping each x-value to a list
                                                  of measured fidelities from multiple runs.
        num_qubits (int): The number of qubits.

    Returns:
        Dict[str, Any]: A dictionary containing the fitted parameters 'A', 'p', 'B', and the 'epc'.
    """
    # Calculate the average fidelity for each x-value.
    avg_fidelities = np.array([np.mean(fidelities_by_x[x]) for x in x_values], dtype=float)
    
    # Provide sensible initial guesses and bounds for the fitting algorithm.
    # This helps the optimizer find a physically meaningful solution.
    # A≈1, p≈0.999 (high fidelity per cycle), B≈0.
    initial_guesses = [1.0, 0.999, 0.0]
    bounds = ([0.0, 0.0, -0.1], [1.5, 1.0, 0.3]) # ([min_A, min_p, min_B], [max_A, max_p, max_B])

    try:
        # Use scipy's curve_fit to find the best-fit parameters.
        params, _ = curve_fit(
            _exp_decay,
            xdata=np.asarray(x_values, dtype=float),
            ydata=avg_fidelities,
            p0=initial_guesses,
            bounds=bounds
        )
    except RuntimeError:
        # If the fit fails to converge, log a warning and return the initial guesses.
        logging.warning("XEB exponential decay fit failed. Using default parameters.")
        params = initial_guesses

    A_fit, p_fit, B_fit = params
    # The Error Per Cycle (EPC) is defined as 1 - p.
    epc = 1.0 - p_fit

    # Return the results in a structured dictionary.
    return {'A': A_fit, 'p': p_fit, 'B': B_fit, 'epc': epc}

def plot_xeb_decay(
    raw_data: Dict[int, List[float]],
    fit_results: Dict[str, float],
    ax: Optional[plt.Axes] = None,
    **plot_kwargs
) -> None:
    """
    Plots the XEB fidelity decay data points and the exponential fit curve.

    Args:
        raw_data (Dict[int, List[float]]): Dictionary mapping x-values to lists of fidelities.
        fit_results (Dict[str, float]): Dictionary containing the fitted parameters from fit_xeb_decay.
        ax (Optional[plt.Axes]): A matplotlib Axes object to plot on. If None, a new figure and axes are created.
        **plot_kwargs: Additional keyword arguments passed to the plot commands (e.g., 'label', 'color').
    """
    # If no Axes object is provided, create a new figure to draw on.
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        show_plot = True # Flag to call plt.show() at the end.
    else:
        show_plot = False # We are drawing on a pre-existing Axes.

    # Prepare data for plotting
    x_values = sorted(raw_data.keys())
    avg_fidelities = [np.mean(raw_data[d]) for d in x_values]
    # Calculate standard error of the mean for error bars. Handle case of single data point.
    err_fidelities = [sem(raw_data[d]) if len(raw_data[d]) > 1 else 0 for d in x_values]

    # Plot the experimental data points with error bars.
    ax.errorbar(x_values, avg_fidelities, yerr=err_fidelities, fmt='o', capsize=5, label=plot_kwargs.get('label', 'XEB Fidelity'))

    # Extract fit parameters
    A, p, B = fit_results['A'], fit_results['p'], fit_results['B']
    epc = fit_results.get('epc', 1.0 - p)
    
    # Generate a smooth curve for the fit function
    fit_x = np.linspace(min(x_values), max(x_values), 200)
    fit_fidelities = _exp_decay(fit_x, A, p, B)
    
    # Create a label for the fit line including key parameters.
    fit_label = f'Fit: $p={p:.4f}$, EPC$={epc:.5f}$' # Increased precision for display
    ax.plot(fit_x, fit_fidelities, '--', color=plot_kwargs.get('color', 'C0'), label=fit_label)

    # --- [v2.1 Change] ---
    # Set a more generic and descriptive label for the x-axis. This was the key update in this version.
    ax.set_xlabel("Noise Exponent (e.g., Native Gate Count)")
    # --- [End of Change] ---
    
    ax.set_ylabel("Fidelity")
    ax.set_title("XEB Fidelity vs. Noise Exponent")
    ax.grid(True, linestyle=':')
    ax.legend()

    # If this function created its own figure, display it.
    if show_plot:
        plt.tight_layout()
        plt.show()

# --- High-Level Orchestrator ---

def analyze_xeb_and_spb_from_results(
    results_by_x: Dict[int, List[Tuple[Dict, Dict]]], # Renamed for clarity
    num_qubits: int
) -> Dict[str, Any]:
    """
    Performs a full XEB and Speckle Purity Benchmarking (SPB) analysis from raw experimental results.

    This function serves as the main entry point. It takes the raw data from an experiment,
    calculates fidelities and purities for each run, and then fits the decay curves for both metrics.

    Args:
        results_by_x (Dict[int, List[Tuple[Dict, Dict]]]): A dictionary where keys are the x-values (e.g., depths)
            and values are lists of experiment runs. Each run is a tuple containing:
            (ideal_probabilities_dict, noisy_counts_dict).
        num_qubits (int): The number of qubits in the experiment.

    Returns:
        Dict[str, Any]: A nested dictionary containing the complete analysis results for
                        both XEB and SPB, including raw data and fit results.
    """
    # Use defaultdict to simplify appending to lists for new keys.
    fidelities_by_x = defaultdict(list)
    purities_by_x = defaultdict(list)
    x_values = sorted(results_by_x.keys())

    # Iterate over each x-value (e.g., each circuit depth).
    for x in x_values:
        results_list = results_by_x[x]
        
        # For each x-value, iterate through all the circuit instances that were run.
        for ideal_probs, noisy_counts in results_list:
            # Calculate and store the XEB fidelity for this specific run.
            fidelities_by_x[x].append(
                analyze_xeb_fidelity(ideal_probs, noisy_counts, num_qubits)
            )
            # Calculate and store the speckle purity for this specific run.
            purities_by_x[x].append(
                analyze_speckle_purity(ideal_probs, noisy_counts, num_qubits)
            )

    # After collecting all data points, perform the exponential decay fitting.
    xeb_fit_results = fit_xeb_decay(x_values, fidelities_by_x, num_qubits)
    spb_fit_results = fit_spb_decay(x_values, purities_by_x)

    # Organize all results into a final, structured dictionary and return it.
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