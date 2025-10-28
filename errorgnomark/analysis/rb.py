# File Path: errorgnomark/analysis/rb.py
# [DEFINITIVE VERSION - Interface matched to user's provided legacy code]

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from typing import Dict, List, Optional, Any, Tuple

# --- Constants ---
MAX_CURVE_FIT_EVALS = 5000  # Maximum number of function evaluations for curve_fit.

# --- Core Analysis Functions ---

def fit_rb_data(survivals: Dict[int, List[float]], num_qubits: int) -> Dict[str, Any]:
    """
    Fits survival probability data from an RB experiment to an exponential decay.
    The fit function is of the form: f(m) = A * p^m + B.

    Args:
        survivals: A dictionary mapping sequence depths (int) to a list of
                   survival probabilities (float).
        num_qubits: The number of qubits in the experiment.

    Returns:
        A dictionary containing the fit parameters, calculated Error Per Clifford (EPC),
        and processed data points. If the fit fails, 'fit_successful' is False.
    """
    depths = np.array(sorted(survivals.keys()))
    means = np.array([np.mean(survivals[d]) for d in depths])
    # Ensure std_errors is non-zero for single-point data to avoid curve_fit errors.
    std_errors = np.array([
        np.std(survivals[d]) / np.sqrt(len(survivals[d])) if len(survivals[d]) > 1 else 1.0
        for d in depths
    ])

    def decay_func(m: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
        """Exponential decay model for Randomized Benchmarking."""
        return A * (p**m) + B

    try:
        d = 2**num_qubits
        # Initial guess for parameters [A, p, B]
        initial_guess = [1 - 1/d, 0.99, 1/d]
        # Bounds for parameters [A, p, B]
        bounds = ([0, 0, 0], [1, 1, 1])
        
        params, _ = curve_fit(
            decay_func,
            depths,
            means,
            p0=initial_guess,
            sigma=std_errors,
            bounds=bounds,
            maxfev=MAX_CURVE_FIT_EVALS,
            absolute_sigma=True
        )
        A, p, B = params
        epc = ((d - 1) / d) * (1 - p)
        fit_successful = True
    except RuntimeError:
        # If the fit fails, return placeholder values.
        A, p, B, epc = 0.0, 0.0, 0.0, 1.0
        fit_successful = False

    return {
        'fit_successful': fit_successful,
        'A': A, 'p': p, 'B': B, 'epc': epc,
        'depths': depths.tolist(),
        'means': means.tolist(),
        'std_errors': std_errors.tolist()
    }

def calculate_epg(p_std: float, p_int: float, num_qubits: int) -> float:
    """
    Calculates the Error Per Gate (EPG) from standard and interleaved decay parameters.
    """
    d = 2**num_qubits
    if p_std == 0:
        return 1.0  # Avoid division by zero
    return ((d - 1) / d) * (1 - p_int / p_std)

def analyze_epg(results_std: Dict, results_int: Dict, num_qubits: int) -> Dict[str, Any]:
    """
    Analyzes results from a full interleaved RB experiment to find the gate error.
    """
    gate_error = float('nan')
    if results_std.get('fit_successful') and results_int.get('fit_successful'):
        gate_error = calculate_epg(results_std['p'], results_int['p'], num_qubits)

    return {
        'gate_error': gate_error,
        'standard_results': results_std,
        'interleaved_results': results_int,
    }

# --- Plotting Functions (Interface Matched to User's Provided File) ---

def plot_rb_single(results: Dict, num_qubits: int, title: str, ax: Optional[plt.Axes] = None) -> plt.Figure:
    """
    Plots the results of a single standard RB experiment on a given axes object.
    If no axes is provided, a new figure is created.

    Args:
        results (Dict): The dictionary returned by fit_rb_data.
        num_qubits (int): The number of qubits in the experiment.
        title (str): The title for the plot.
        ax (Optional[plt.Axes]): A matplotlib Axes object to draw on. If None,
                                 a new figure and axes are created.
    
    Returns:
        plt.Figure: The figure object containing the plot.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.get_figure()

    if results['fit_successful']:
        label = f"Data (EPC = {results['epc']:.2e})"
        x_fit = np.linspace(0, max(results['depths']), 200)
        ax.plot(x_fit, results['A'] * (results['p']**x_fit) + results['B'], 'r--', label="Exponential Fit")
    else:
        label = "Data (Fit Failed)"

    ax.errorbar(results['depths'], results['means'], yerr=results['std_errors'], fmt='o', capsize=5, label=label)
    ax.set_title(title, fontsize=16)
    ax.set_xlabel("Clifford Sequence Depth (m)", fontsize=12)
    ax.set_ylabel("Ground State Survival Probability", fontsize=12)
    ax.legend()
    ax.grid(True, linestyle='--')
    
    fig.tight_layout()
    return fig

def plot_rb_comparison(results_std: Dict, results_int: Dict, num_qubits: int, target_gate_name: str, ax: Optional[plt.Axes] = None) -> plt.Figure:
    """
    Plots a comparison between a standard and an interleaved RB experiment on a given axes object.
    If no axes is provided, a new figure is created.

    Args:
        results_std (Dict): The fit results for the standard RB experiment.
        results_int (Dict): The fit results for the interleaved RB experiment.
        num_qubits (int): The number of qubits.
        target_gate_name (str): The name of the interleaved gate.
        ax (Optional[plt.Axes]): A matplotlib Axes object to draw on.
    
    Returns:
        plt.Figure: The figure object containing the plot.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.get_figure()

    # Plot Standard RB data and fit
    if results_std.get('fit_successful'):
        ax.errorbar(
            results_std['depths'], results_std['means'], yerr=results_std['std_errors'],
            fmt='o', capsize=5, color='darkblue', ecolor='darkblue',
            label=f"Standard (EPC={results_std['epc']:.2e})"
        )
        x_fit = np.linspace(0, max(results_std['depths']), 200)
        ax.plot(x_fit, results_std['A'] * (results_std['p']**x_fit) + results_std['B'], '--', color='royalblue')

    # Plot Interleaved RB data and fit
    if results_int.get('fit_successful'):
        epg = calculate_epg(results_std.get('p', 0), results_int.get('p', 0), num_qubits) if results_std.get('fit_successful') else float('nan')
        label_int = f"Interleaved (EPG={epg:.2e})" if not np.isnan(epg) else "Interleaved (EPG Calc Failed)"
        ax.errorbar(
            results_int['depths'], results_int['means'], yerr=results_int['std_errors'],
            fmt='s', capsize=5, color='darkred', ecolor='darkred', label=label_int
        )
        x_fit_int = np.linspace(0, max(results_int['depths']), 200)
        ax.plot(x_fit_int, results_int['A'] * (results_int['p']**x_fit_int) + results_int['B'], '--', color='lightcoral')

    ax.set_title(f"Interleaved RB for '{target_gate_name}' ({num_qubits}Q)", fontsize=16)
    ax.set_xlabel("Clifford Sequence Depth (m)", fontsize=12)
    ax.set_ylabel("Ground State Survival Probability", fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, linestyle='--')
    
    fig.tight_layout()
    return fig