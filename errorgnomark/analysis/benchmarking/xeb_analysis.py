# File Path: errorgnomark/analysis/benchmarking/xeb_analysis.py
# FINAL ROBUST VERSION: The logic is sound, but we add a normalization step
# to `analyze_xeb_fidelity` as a defensive measure against floating point errors.

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from typing import Dict, List, Tuple, Optional, Any

# ==============================================================================
# --- Analysis Functions ---
# ==============================================================================

def analyze_xeb_fidelity(ideal_probabilities: Dict[str, float], noisy_counts: Dict[str, int]) -> float:
    """
    Calculates the linear cross-entropy fidelity from theoretical ideal
    probabilities and experimental noisy counts.
    """
    if not noisy_counts: return 0.0
    total_shots = sum(noisy_counts.values())
    if total_shots == 0: return 0.0
    
    num_qubits = len(next(iter(noisy_counts.keys())))

    # --- [DEFENSIVE NORMALIZATION] ---
    # Ensure the provided ideal probabilities sum to 1.0 to prevent floating
    # point errors from affecting the fidelity calculation.
    prob_sum = sum(ideal_probabilities.values())
    if not np.isclose(prob_sum, 1.0):
        # This print can be helpful for debugging if normalization issues occur.
        # print(f"Warning: Normalizing ideal probabilities (sum was {prob_sum:.6f}).")
        for k in ideal_probabilities:
            ideal_probabilities[k] /= prob_sum
    # --- [END OF NORMALIZATION] ---

    # Calculate the mean probability of measured bitstrings according to the ideal distribution.
    mean_ideal_prob = sum(
        ideal_probabilities.get(bitstring, 0) * count for bitstring, count in noisy_counts.items()
    ) / total_shots
    
    # Standard XEB fidelity formula.
    fidelity = (2**num_qubits) * mean_ideal_prob - 1
    return fidelity

def fit_xeb_fidelity_decay(fidelities: Dict[int, List[float]]) -> Dict:
    """
    Fits XEB fidelity data to an exponential decay model: A * p^m + B.
    """
    if not fidelities:
        return {'p': np.nan, 'A': np.nan, 'B': np.nan, 'error_per_gate': np.nan, 'fit_successful': False, 'r_squared': 0}
    
    depths = np.array(list(fidelities.keys()))
    mean_fidelities = np.array([np.mean(f) for f in fidelities.values()])
    
    # Filter out any potential NaN values from failed fidelity calculations
    valid_indices = ~np.isnan(mean_fidelities)
    if not np.any(valid_indices):
        return {'p': np.nan, 'A': np.nan, 'B': np.nan, 'error_per_gate': np.nan, 'fit_successful': False, 'r_squared': 0}
    
    depths = depths[valid_indices]
    mean_fidelities = mean_fidelities[valid_indices]

    def decay_model(m, p, A, B):
        return A * (p**m) + B
        
    initial_guess = [0.99, 1.0, 0.0]
    bounds = ([0, 0, -1], [1, 2, 1])
    
    try:
        params, cov = curve_fit(decay_model, depths, mean_fidelities, p0=initial_guess, bounds=bounds, maxfev=5000)
        p, A, B = params
        
        residuals = mean_fidelities - decay_model(depths, *params)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((mean_fidelities - np.mean(mean_fidelities))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        error_per_gate = 1 - p
        return {'p': p, 'A': A, 'B': B, 'error_per_gate': error_per_gate, 'fit_successful': True, 'r_squared': r_squared}
    except (RuntimeError, ValueError):
        return {'p': np.nan, 'A': np.nan, 'B': np.nan, 'error_per_gate': np.nan, 'fit_successful': False, 'r_squared': 0}

# ==============================================================================
# --- Plotting Function (No changes needed, already robust) ---
# ==============================================================================

def plot_xeb_fit(fidelities: Dict[int, List[float]], 
                 fit_results: Dict[str, Any], 
                 title_info: str = "", 
                 ax: Optional[plt.Axes] = None, 
                 save_path: Optional[str] = None):
    """
    Plots the XEB fidelity data points and the fitted decay curve.
    """
    show_plot = (ax is None) and (save_path is None)
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    else:
        fig = ax.get_figure()

    depths = np.array(list(fidelities.keys()))
    mean_fidelities = np.array([np.mean(f) for f in fidelities.values()])
    std_fidelities = np.array([np.std(f) for f in fidelities.values()])

    ax.errorbar(depths, mean_fidelities, yerr=std_fidelities, fmt='o', capsize=5, label='Data (Mean ± Std Dev)', color='purple', zorder=10)

    if fit_results.get('fit_successful', False):
        fine_depths = np.linspace(min(depths), max(depths), 200)
        p, A, B = fit_results['p'], fit_results['A'], fit_results['B']
        def decay_model(m, p, A, B): return A * (p**m) + B
        fit_curve = decay_model(fine_depths, p, A, B)
        error_str = f"Error/Gate = {fit_results['error_per_gate']:.2e}"
        r2_str = f"R² = {fit_results.get('r_squared', 0):.3f}"
        ax.plot(fine_depths, fit_curve, '-', label=f"Fit ({error_str}, {r2_str})", color='crimson', linewidth=2)

    ax.set_xlabel("Circuit Depth")
    ax.set_ylabel("XEB Fidelity")
    title = f"XEB Fidelity Decay"
    if title_info: title += f" {title_info}"
    ax.set_title(title)
    ax.legend()
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    if save_path:
        fig.savefig(save_path, bbox_inches='tight', dpi=300)
    if show_plot:
        plt.tight_layout()
        plt.show()