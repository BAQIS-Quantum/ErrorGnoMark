# File Path: errorgnomark/analysis/spb.py
#
# [COMPATIBILITY UPDATE v3.1 - Added Adapters for XEB/SPB Dual Analysis]

import logging
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import sem

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Core Analysis Function ---

def _calculate_purity_from_counts(counts: Dict[str, int], shots: int) -> float:
    """Calculates purity using the standard UNBIASED ESTIMATOR for SPB."""
    if shots < 2:
        return np.nan
    n_i = np.array(list(counts.values()))
    N = shots
    sum_p_sq_hat = np.sum(n_i * (n_i - 1)) / (N * (N - 1))
    return sum_p_sq_hat

# <<< NEW FUNCTION START: Public API for per-circuit purity calculation >>>
# This is the function that xeb.py is trying to import. It acts as a public
# wrapper around your internal _calculate_purity_from_counts function.
def analyze_speckle_purity(
    ideal_probs: Dict[str, float], 
    noisy_counts: Dict[str, int], 
    num_qubits: int
) -> float:
    """
    Calculates the speckle purity for a single circuit run.
    
    This function matches the interface expected by `analyze_xeb_and_spb_from_results`.
    The unbiased estimator for purity only requires the noisy counts.
    """
    total_shots = sum(noisy_counts.values())
    # The other arguments (ideal_probs, num_qubits) are ignored by this specific
    # purity calculation method, but are included for a consistent API with XEB.
    return _calculate_purity_from_counts(noisy_counts, total_shots)
# <<< NEW FUNCTION END >>>


# --- Fitting and Plotting Functions ---

def _exp_decay_spb(x: np.ndarray, A: float, p_c: float, B: float) -> np.ndarray:
    """Exponential decay function for SPB fitting: P(m) = A * (p_c)^m + B."""
    return A * (p_c**x) + B

def fit_spb_data(
    purities_by_depth: Dict[int, List[float]],
    num_qubits: int
) -> Dict[str, Any]:
    """
    Fits the speckle purity decay to an exponential model.
    The structure of the returned dictionary is crucial for compatibility.
    """
    depth_keys = sorted(purities_by_depth.keys())
    if not depth_keys:
        return {'fit_successful': False, 'raw_data': purities_by_depth}
        
    avg_purities = np.array([np.mean(purities_by_depth[d]) for d in depth_keys])
    
    d = 2**num_qubits
    B0 = 1 / d

    initial_guesses = [1.0 - B0, 0.99, B0]

    try:
        params, cov = curve_fit(
            _exp_decay_spb, xdata=depth_keys, ydata=avg_purities,
            p0=initial_guesses, bounds=([0, 0, 0], [2.0, 1.0, 1.0])
        )
        fit_successful = True
        perr = np.sqrt(np.diag(cov))
    except RuntimeError:
        logging.warning("SPB exponential decay fit failed. Using default parameters.")
        params = initial_guesses
        perr = [np.inf, np.inf, np.inf]
        fit_successful = False

    A_fit, p_c_fit, B_fit = params

    # The returned dictionary contains both fit results and raw data,
    # which can then be passed to plotting functions.
    fit_results = {
        'A': A_fit, 'p_c': p_c_fit, 'B': B_fit,
        'A_err': perr[0], 'p_c_err': perr[1], 'B_err': perr[2],
    }
    
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
# signature and return value. It works by calling your existing `fit_spb_data`
# function and extracting the part of the result that the plotting function needs.
def fit_spb_decay(
    x_values: List[int],
    purities_by_x: Dict[int, List[float]]
) -> Dict[str, Any]:
    """
    Adapter function to fit SPB decay.
    
    This function matches the simple interface expected by `analyze_xeb_and_spb_from_results`.
    It fits the data and returns only the core fit parameters dictionary.
    Since `num_qubits` is not passed, we use a reasonable default for the fit's
    initial guess, which is generally robust.
    """
    x_keys = sorted(purities_by_x.keys())
    if not x_keys:
        return {'A': 1.0, 'p_c': 1.0, 'B': 0.0} # Return default on empty data
        
    avg_purities = np.array([np.mean(purities_by_x[x]) for x in x_keys])
    
    # Use robust initial guesses that don't depend on num_qubits
    initial_guesses = [1.0, 0.99, 0.0]

    try:
        params, _ = curve_fit(
            _exp_decay_spb, xdata=x_keys, ydata=avg_purities,
            p0=initial_guesses, bounds=([0, 0, -0.1], [2.0, 1.0, 1.0])
        )
    except RuntimeError:
        logging.warning("SPB exponential decay fit failed. Using default parameters.")
        params = initial_guesses

    A_fit, p_c_fit, B_fit = params

    # Return the simple dictionary that plot_spb_decay expects
    return {'A': A_fit, 'p_c': p_c_fit, 'B': B_fit}
# <<< NEW FUNCTION END >>>


def plot_spb_decay(
    raw_data: Dict[int, List[float]],
    fit_results: Dict[str, float],
    ax: Optional[plt.Axes] = None,
    **plot_kwargs
) -> None:
    """
    [COMPATIBILITY UPDATE] Plots SPB decay. Signature matches XEBExperiment's expectation.
    Accepts raw_data and fit_results dictionaries separately.
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
    color = plot_kwargs.get('color') # Use matplotlib's default cycle if not provided
    
    ax.errorbar(depths, avg_purities, yerr=err_purities, fmt='o', capsize=5, label=label, color=color)

    # Note: The key for the decay parameter is 'p_c' in your file
    A, p_c, B = fit_results['A'], fit_results['p_c'], fit_results['B']
    
    fit_depths = np.linspace(min(depths), max(depths), 200)
    fit_purities = _exp_decay_spb(fit_depths, A, p_c, B)
    
    fit_label = f'Fit ($p_c={p_c:.4f}$)'
    # If a color was specified for data, use it for the fit line too.
    ax.plot(fit_depths, fit_purities, '--', label=fit_label, color=ax.get_lines()[-1].get_color() if color is None else color)

    # Use the more general x-axis label consistent with the previous fix
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
    """Plots standard and interleaved SPB results on the same axes."""
    fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    
    # Plot standard data using the new compatible plot_spb_decay function
    if std_results.get('fit_successful'):
        plot_spb_decay(std_results['raw_data'], std_results['fit_results'], ax=ax, label='Standard SPB', color='C0')
    
    # Plot interleaved data
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
    """Calculates gate purity and error from standard and interleaved SPB results."""
    std_fit = results_std.get('fit_results', {})
    int_fit = results_int.get('fit_results', {})
    
    p_c_std = std_fit.get('p_c')
    p_c_int = int_fit.get('p_c')

    if p_c_std is None or p_c_int is None:
        return {'calculation_successful': False, 'reason': 'One or both fits failed.'}

    # Ensure p_c_std is not zero to avoid division errors
    if p_c_std == 0:
        return {'calculation_successful': False, 'reason': 'Standard purity decay factor is zero.'}

    p_G = p_c_int / p_c_std
    d_sq = (2**num_qubits)**2
    gate_error = (1 - p_G) * d_sq / (d_sq - 1)

    return {
        'calculation_successful': True,
        'p_G': p_G,
        'gate_error': gate_error
    }