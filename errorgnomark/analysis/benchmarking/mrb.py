# errorgnomark/analysis/benchmarking/mrb.py

import numpy as np
from typing import Dict, List, Tuple, Union
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# Imports for heatmap visualization
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Set plot styling for consistency
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def _mrb_decay_func(m: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """
    Defines the exponential decay model for Randomized Benchmarking.
    F(m) = A * p^m + B
    """
    return A * (p**m) + B

def fit_mrb_decay(survival_data: Dict[int, List[float]], num_qubits: int) -> Dict:
    """
    Fits the survival probability data to the MRB decay model.
    """
    depths = np.array(sorted(survival_data.keys()))
    mean_survivals = np.array([np.mean(survival_data[d]) for d in depths])
    std_survivals = np.array([np.std(survival_data[d]) / np.sqrt(len(survival_data[d])) for d in depths])

    p0 = [mean_survivals[0] - mean_survivals[-1], 0.99, mean_survivals[-1]]

    try:
        params, params_covariance = curve_fit(
            _mrb_decay_func,
            depths,
            mean_survivals,
            p0=p0,
            sigma=std_survivals,
            maxfev=10000
        )
        fit_successful = True
        A, p, B = params
        param_errors = np.sqrt(np.diag(params_covariance))
        d = 2**num_qubits
        avg_gate_error = (d - 1) * (1 - p) / d

    except RuntimeError:
        fit_successful = False
        A, p, B = (np.nan, np.nan, np.nan)
        avg_gate_error = np.nan
        params = (np.nan, np.nan, np.nan)
        param_errors = (np.nan, np.nan, np.nan)

    return {
        "fit_successful": fit_successful,
        "A": A,
        "p": p,
        "B": B,
        "average_gate_error": avg_gate_error,
        "params": params,
        "param_errors": param_errors
    }

def plot_mrb_fit(survival_data: Dict[int, List[float]], fit_results: Dict, num_qubits: int, save_path: str = None):
    """
    Plots the MRB data and the corresponding fit curve.
    """
    depths = np.array(sorted(survival_data.keys()))
    mean_survivals = np.array([np.mean(survival_data[d]) for d in depths])
    std_survivals = np.array([np.std(survival_data[d]) / np.sqrt(len(survival_data[d])) for d in depths])

    plt.figure(figsize=(10, 6))
    plt.errorbar(depths, mean_survivals, yerr=std_survivals, fmt='o', capsize=5, label='Mean Survival Probability')

    if fit_results['fit_successful']:
        plot_depths = np.linspace(0, max(depths), 200)
        A, p, B = fit_results['params']
        plt.plot(plot_depths, _mrb_decay_func(plot_depths, A, p, B), 'r-', 
                 label=f'Fit: $F = A \\cdot p^m + B$\n'
                       f'$p$ = {p:.4f}\n'
                       f'Avg Gate Error = {fit_results["average_gate_error"]:.2e}')

    plt.xlabel("Clifford Sequence Depth (m)")
    plt.ylabel("Survival Probability")
    plt.title(f"Mirror Randomized Benchmarking for {num_qubits} Qubit(s)")
    plt.legend()
    plt.grid(True, which='both', linestyle='--')
    
    if save_path:
        plt.savefig(save_path, dpi=300)
        print(f"Figure saved as {save_path}")
        plt.close()
    else:
        plt.show()

# ==============================================================================
# --- MODIFIED Heatmap Plotting Function ---
# ==============================================================================

def plot_mrb_heatmap(
    polarization_results: List[List[float]],
    qubit_groups: List[Union[int, Tuple[int, ...]]],
    depths: List[int],
    title: str = "MRBQM Heatmap (Effective polarization)",
    colorbar_label: str = "Effective Polarization",
    # --- [THE ONLY CHANGE IS HERE] ---
    # Changed from 'Blues_r' to 'Blues' as requested.
    # Now, larger values will be darker blue.
    cmap: str = 'Blues',
    save_path: str = None
):
    """
    Creates a heatmap to visualize direct MRB results.
    This function plots 'Number of Qubits' on the x-axis and 'Circuit Depth' on the y-axis.
    """
    grid = np.array(polarization_results).T
    
    if grid.shape != (len(depths), len(qubit_groups)):
        raise ValueError(
            f"Shape of transposed polarization_results {grid.shape} does not match the dimensions "
            f"provided by depths ({len(depths)}) and qubit_groups ({len(qubit_groups)})."
        )

    num_qubits_labels = [len(q) if isinstance(q, tuple) else 1 for q in qubit_groups]

    fig, ax = plt.subplots(figsize=(max(8, len(qubit_groups) * 1.8), max(6, len(depths) * 0.6)))

    masked_grid = np.ma.masked_where(np.isnan(grid), grid)
    vmin = np.nanmin(grid) if not np.all(np.isnan(grid)) else 0
    vmax = np.nanmax(grid) if not np.all(np.isnan(grid)) else 1

    im = ax.imshow(masked_grid, cmap=cmap, interpolation='nearest', vmin=vmin, vmax=vmax, aspect='auto')

    ax.set_xticks(np.arange(grid.shape[1] + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(grid.shape[0] + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="white", linestyle='-', linewidth=2)
    ax.tick_params(which="minor", size=0)

    ax.set_xticks(np.arange(grid.shape[1]))
    ax.set_yticks(np.arange(grid.shape[0]))
    ax.set_xticklabels(num_qubits_labels)
    ax.set_yticklabels([str(d) for d in depths])

    ax.invert_yaxis()

    ax.set_title(title, fontsize=20, pad=20)
    ax.set_xlabel("Number of Qubits", fontsize=16)
    ax.set_ylabel("Circuit Depth", fontsize=16)
    ax.tick_params(axis='both', which='major', labelsize=14)

    for row in range(grid.shape[0]):
        for col in range(grid.shape[1]):
            if not np.isnan(grid[row, col]):
                value = grid[row, col]
                # This logic automatically chooses black or white text for readability.
                # For 'Blues', high values are dark, norm is high -> white text.
                # Low values are light, norm is low -> black text.
                text_color = "white" if im.norm(value) > 0.5 else "black"
                ax.text(col, row, f'{value:.4f}', ha='center', va='center', color=text_color, fontsize=12)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.2)
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label(colorbar_label, rotation=270, labelpad=25, fontsize=16)
    cbar.ax.tick_params(labelsize=14)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    if save_path:
        plt.savefig(save_path, dpi=300)
        print(f"Figure saved as {save_path}")
        plt.close()
    else:
        plt.show()