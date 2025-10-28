# File Path: errorgnomark/analysis/spb.py
#
# [COMPATIBILITY UPDATE v3.1 - Added Adapters for XEB/SPB Dual Analysis]
# Description: This module provides functions for Speckle Purity Benchmarking (SPB).
# It includes core purity calculation, fitting the purity decay to an exponential model,
# and plotting the results. This version has been specifically updated with adapter
# functions to ensure a compatible interface with the dual XEB/SPB analysis workflow
# orchestrated by the `xeb.py` module.

import logging
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import sem

# Configure a basic logger for informational and warning messages.
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Core Analysis Function ---

def _calculate_purity_from_counts(counts: Dict[str, int], shots: int) -> float:
    """
    Calculates purity using the standard UNBIASED ESTIMATOR for SPB.

    This estimator, sum(n_i * (n_i - 1)) / (N * (N - 1)), corrects for the statistical
    bias that arises from estimating probabilities from a finite number of shots (N).
    It effectively measures the collision probability in the output distribution.

    Args:
        counts (Dict[str, int]): A dictionary of measured bitstring counts.
        shots (int): The total number of measurement shots (N).

    Returns:
        float: The calculated unbiased purity. Returns np.nan if shots < 2.
    """
    # The unbiased estimator is undefined for fewer than 2 shots.
    if shots < 2:
        return np.nan
    
    # n_i represents the array of counts for each measured bitstring.
    n_i = np.array(list(counts.values()))
    N = shots
    
    # Calculate the sum of P_i^2 using the unbiased estimator formula.
    sum_p_sq_hat = np.sum(n_i * (n_i - 1)) / (N * (N - 1))
    return sum_p_sq_hat

# <<< NEW FUNCTION START: Public API for per-circuit purity calculation >>>
# This is the function that xeb.py is trying to import. It acts as a public
# wrapper around the internal _calculate_purity_from_counts function.
def analyze_speckle_purity(
    ideal_probs: Dict[str, float], 
    noisy_counts: Dict[str, int], 
    num_qubits: int
) -> float:
    """
    Calculates the speckle purity for a single circuit run.
    
    This function matches the interface expected by `analyze_xeb_and_spb_from_results` in xeb.py.
    The unbiased estimator for purity only requires the noisy counts. The other arguments
    are included for API consistency with the XEB fidelity calculation but are ignored here.

    Args:
        ideal_probs (Dict[str, float]): Ignored. Present for API compatibility.
        noisy_counts (Dict[str, int]): A dictionary of measured bitstring counts.
        num_qubits (int): Ignored. Present for API compatibility.

    Returns:
        float: The calculated speckle purity for the run.
    """
    total_shots = sum(noisy_counts.values())
    # This specific purity calculation method is "blind" to the ideal probabilities.
    # It only depends on the statistical properties of the measured output distribution.
    return _calculate_purity_from_counts(noisy_counts, total_shots)
# <<< NEW FUNCTION END >>>


# --- Fitting and Plotting Functions ---

def _exp_decay_spb(x: np.ndarray, A: float, p_c: float, B: float) -> np.ndarray:
    """
    Exponential decay function for SPB fitting: P(m) = A * (p_c)^m + B.
    - P(m): Purity as a function of noise exponent 'm' (e.g., depth).
    - A: Amplitude.
    - p_c: Purity decay parameter per cycle. This is the key value extracted from the fit.
    - B: Asymptotic offset, ideally 1/2^N for a fully depolarized state.
    """
    return A * (p_c**x) + B

def fit_spb_data(
    purities_by_depth: Dict[int, List[float]],
    num_qubits: int
) -> Dict[str, Any]:
    """
    Fits the speckle purity decay to an exponential model.
    This is a comprehensive fitting function that returns a detailed summary.

    Args:
        purities_by_depth (Dict[int, List[float]]): Dictionary mapping depth to purity measurements.
        num_qubits (int): The number of qubits, used to estimate the asymptotic offset.

    Returns:
        Dict[str, Any]: A dictionary containing fit success status, fit parameters with errors,
                        and the raw data used for the fit.
    """
    depth_keys = sorted(purities_by_depth.keys())
    if not depth_keys:
        logging.warning("Cannot fit SPB data: input dictionary is empty.")
        return {'fit_successful': False, 'raw_data': purities_by_depth}
        
    avg_purities = np.array([np.mean(purities_by_depth[d]) for d in depth_keys])
    
    # The theoretical asymptotic purity for a uniform distribution is 1/d where d=2^N.
    d = 2**num_qubits
    B0 = 1 / d

    # Initial guesses for the fit parameters [A, p_c, B].
    initial_guesses = [1.0 - B0, 0.99, B0]

    try:
        # Perform the curve fitting.
        params, cov = curve_fit(
            _exp_decay_spb, xdata=depth_keys, ydata=avg_purities,
            p0=initial_guesses, bounds=([0, 0, 0], [2.0, 1.0, 1.0])
        )
        fit_successful = True
        # Calculate the standard error for each parameter.
        perr = np.sqrt(np.diag(cov))
    except RuntimeError:
        logging.warning("SPB exponential decay fit failed. Using default parameters.")
        params = initial_guesses
        perr = [np.inf, np.inf, np.inf] # Indicate failure with infinite error.
        fit_successful = False

    A_fit, p_c_fit, B_fit = params

    # Structure the fit results.
    fit_results = {
        'A': A_fit, 'p_c': p_c_fit, 'B': B_fit,
        'A_err': perr[0], 'p_c_err': perr[1], 'B_err': perr[2],
    }
    
    # Compile a complete summary of the analysis.
    analysis_summary = {
        'fit_successful': fit_successful,
        'fit_results': fit_results,
        'raw_data': purities_by_depth,
        'depths': depth_keys,
        'avg_purities': avg_purities,
    }
    return analysis_summary

# <<< NEW FUNCTION START: Adapter for the fitting function >>>
# This function, `fit_spb_decay`, is what xeb.py calls. It has a simpler
# signature and return value. It acts as a bridge to make the SPB fitting
# compatible with the orchestration logic in `analyze_xeb_and_spb_from_results`.
def fit_spb_decay(
    x_values: List[int],
    purities_by_x: Dict[int, List[float]]
) -> Dict[str, Any]:
    """
    Adapter function to fit SPB decay, providing a simplified API.
    
    This function matches the simpler interface expected by `analyze_xeb_and_spb_from_results`.
    It fits the data and returns only the core fit parameters dictionary required by the
    plotting functions. It uses robust initial guesses that do not require `num_qubits`.

    Args:
        x_values (List[int]): The list of independent variable values (e.g., depths).
        purities_by_x (Dict[int, List[float]]): Dictionary mapping x-value to purity lists.

    Returns:
        Dict[str, Any]: A simple dictionary with the core fit parameters: 'A', 'p_c', 'B'.
    """
    x_keys = sorted(purities_by_x.keys())
    if not x_keys:
        # Return a default, no-decay result if there's no data.
        return {'A': 1.0, 'p_c': 1.0, 'B': 0.0} 
        
    avg_purities = np.array([np.mean(purities_by_x[x]) for x in x_keys])
    
    # Use robust initial guesses that don't depend on num_qubits.
    # This makes the adapter more flexible, though potentially less precise for the 'B' guess.
    initial_guesses = [1.0, 0.99, 0.0]

    try:
        params, _ = curve_fit(
            _exp_decay_spb, xdata=x_keys, ydata=avg_purities,
            p0=initial_guesses, bounds=([0, 0, -0.1], [2.0, 1.0, 1.0])
        )
    except RuntimeError:
        logging.warning("SPB exponential decay fit failed in adapter. Using default parameters.")
        params = initial_guesses

    A_fit, p_c_fit, B_fit = params

    # Return the simple dictionary that the unified plotting functions expect.
    return {'A': A_fit, 'p_c': p_c_fit, 'B': B_fit}
# <<< NEW FUNCTION END >>>


def plot_spb_decay(
    raw_data: Dict[int, List[float]],
    fit_results: Dict[str, float],
    ax: Optional[plt.Axes] = None,
    **plot_kwargs
) -> None:
    """
    [COMPATIBILITY UPDATE] Plots SPB decay with a signature matching the XEB plotter.
    
    This function accepts raw_data and fit_results dictionaries separately to maintain
    a consistent API with `plot_xeb_decay`, allowing them to be used interchangeably.

    Args:
        raw_data (Dict[int, List[float]]): Dictionary mapping x-values to lists of purities.
        fit_results (Dict[str, float]): Dictionary with fit parameters ('A', 'p_c', 'B').
        ax (Optional[plt.Axes]): A matplotlib Axes object to plot on. If None, a new figure is created.
        **plot_kwargs: Additional keyword arguments for plotting (e.g., 'label', 'color', 'title').
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        show_plot = True
    else:
        show_plot = False

    depths = sorted(raw_data.keys())
    if not depths:
        logging.warning("Cannot plot SPB decay: raw_data is empty.")
        return
        
    avg_purities = [np.mean(raw_data[d]) for d in depths]
    err_purities = [sem(raw_data[d]) if len(raw_data[d]) > 1 else 0 for d in depths]

    label = plot_kwargs.get('label', 'Speckle Purity')
    color = plot_kwargs.get('color') # Let matplotlib handle color cycle if not specified.
    
    # Plot the experimental data points with error bars.
    ax.errorbar(depths, avg_purities, yerr=err_purities, fmt='o', capsize=5, label=label, color=color)

    # Note: The key for the decay parameter is 'p_c' in this module.
    A, p_c, B = fit_results['A'], fit_results['p_c'], fit_results['B']
    
    # Generate a smooth curve for the fit.
    fit_depths = np.linspace(min(depths), max(depths), 200)
    fit_purities = _exp_decay_spb(fit_depths, A, p_c, B)
    
    fit_label = f'Fit ($p_c={p_c:.4f}$)'
    # If a color was specified for data, use it for the fit line. If not, match the data point color.
    ax.plot(fit_depths, fit_purities, '--', label=fit_label, color=ax.get_lines()[-1].get_color() if color is None else color)

    # Use the more general x-axis label for consistency with xeb.py.
    ax.set_xlabel("Noise Exponent (e.g., Native Gate Count)")
    ax.set_ylabel("Speckle Purity")
    ax.set_title(plot_kwargs.get('title', "Speckle Purity vs. Noise Exponent"))
    ax.grid(True, linestyle=':')
    ax.legend()

    if show_plot:
        plt.tight_layout()

def plot_spb_comparison(
    std_results: Dict[str, Any],
    int_results: Dict[str, Any],
    num_qubits: int,
    target_gate_name: str
) -> None:
    """
    Plots standard and interleaved SPB results on the same axes for comparison.

    Args:
        std_results (Dict[str, Any]): The analysis summary dictionary from `fit_spb_data` for the standard run.
        int_results (Dict[str, Any]): The analysis summary for the interleaved run.
        num_qubits (int): The number of qubits.
        target_gate_name (str): The name of the interleaved gate, for labeling.
    """
    fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    
    # Plot standard data using the new compatible plot_spb_decay function.
    if std_results.get('fit_successful'):
        plot_spb_decay(std_results['raw_data'], std_results['fit_results'], ax=ax, label='Standard SPB', color='C0')
    
    # Plot interleaved data on the same axes.
    if int_results.get('fit_successful'):
        plot_spb_decay(int_results['raw_data'], int_results['fit_results'], ax=ax, label=f'Interleaved ({target_gate_name})', color='C1')
    
    ax.legend()
    ax.set_title(f"{num_qubits}-Qubit SPB: Standard vs. Interleaved ('{target_gate_name}')")
    plt.tight_layout()

def calculate_spb_gate_error(
    results_std: Dict[str, Any],
    results_int: Dict[str, Any],
    num_qubits: int
) -> Dict[str, Any]:
    """
    Calculates the interleaved gate purity and error from standard and interleaved SPB fits.

    This is the final step in Interleaved Randomized Benchmarking. The error of the reference
    sequence (standard) is divided out from the interleaved sequence to isolate the error
    of the target gate.

    Args:
        results_std (Dict[str, Any]): The analysis summary for the standard run.
        results_int (Dict[str, Any]): The analysis summary for the interleaved run.
        num_qubits (int): The number of qubits.

    Returns:
        Dict[str, Any]: A dictionary with the calculated gate purity (p_G) and gate error.
    """
    std_fit = results_std.get('fit_results', {})
    int_fit = results_int.get('fit_results', {})
    
    p_c_std = std_fit.get('p_c') # Purity decay factor for standard RB
    p_c_int = int_fit.get('p_c') # Purity decay factor for interleaved RB

    if p_c_std is None or p_c_int is None:
        return {'calculation_successful': False, 'reason': 'One or both fits failed.'}

    if p_c_std == 0:
        return {'calculation_successful': False, 'reason': 'Standard purity decay factor is zero.'}

    # Gate purity p_G is the ratio of the decay factors.
    p_G = p_c_int / p_c_std
    
    # Convert gate purity to gate error (average gate fidelity is 1 - gate_error).
    d_sq = (2**num_qubits)**2
    gate_error = (1 - p_G) * (d_sq - 1) / d_sq # Adjusted formula for purity

    return {
        'calculation_successful': True,
        'p_G': p_G,
        'gate_error': gate_error
    }