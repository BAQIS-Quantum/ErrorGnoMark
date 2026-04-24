# File Path: errorgnomark/analysis/mrb.py
# [VERSION 5.0] - Added high-level summary and plotting functions.

"""
Module for analyzing and visualizing Mirrored Randomized Benchmarking (MRB) experiments.

This module provides functions to:
1. Fit the exponential decay of sequence fidelity (survival probability).
2. Compute the Error Per Clifford (EPC) from the fit.
3. Plot and save the survival probability decay curve for individual experiments.
4. Plot and save a scalability heatmap of effective polarization vs. number of qubits and depth.
5. Provide high-level functions to display a summary table and generate all plots from a list of results.
"""

import numpy as np
from typing import Dict, List, Tuple, TypedDict, Optional
from scipy.optimize import curve_fit
import os
import pandas as pd

# This import is needed for the new high-level functions
from egm.analysis.result import AnalysisResult

# Optional imports for plotting. Functions will raise ImportError if not installed.
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    _plotting_enabled = True
except ImportError:
    _plotting_enabled = False


# --- Type Definitions for Clarity ---

class MRBFitResult(TypedDict):
    """
    A dictionary defining the structure of the return value from fit_mrb_decay.
    """
    fit_successful: bool
    A: float
    p: float
    B: float
    epc: float
    epc_err: float
    params: Tuple[float, float, float]
    param_errors: Tuple[float, float, float]
    depths: np.ndarray
    mean_survivals: np.ndarray
    std_errors: np.ndarray


# --- Core Analysis Functions ---

def _mrb_decay_func(m: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """
    Defines the exponential decay model for randomized benchmarking.
    F(m) = A * p^m + B
    """
    return A * (p**m) + B

def fit_mrb_decay(survival_data: Dict[int, List[float]], num_qubits: int) -> MRBFitResult:
    """
    Fits survival probability data to the MRB exponential decay model.

    Args:
        survival_data: A dictionary mapping sequence depth (int) to a list of
                       survival probabilities (float) for that depth.
        num_qubits: The total number of qubits in the benchmarking group.
                    This MUST be an even number.

    Returns:
        A MRBFitResult dictionary containing fit results and processed data.
    """
    if not survival_data or num_qubits % 2 != 0:
        if num_qubits % 2 != 0:
            print(f"Error: num_qubits must be even for MRB analysis, but got {num_qubits}.")
        return _create_failure_result()

    depths = np.array(sorted(survival_data.keys()))
    mean_survivals = np.array([np.mean(survival_data[d]) for d in depths])
    std_errors = np.array([
        np.std(survival_data[d], ddof=1) / np.sqrt(len(survival_data[d]))
        if len(survival_data[d]) > 1 else 1e-9
        for d in depths
    ])

    p0 = [mean_survivals[0] - mean_survivals[-1], 0.99, mean_survivals[-1]]

    try:
        popt, pcov = curve_fit(
            _mrb_decay_func, depths, mean_survivals, p0=p0,
            sigma=std_errors, absolute_sigma=True, maxfev=10000,
            bounds=([0, 0, 0], [1.5, 1.0, 1.0])
        )
        param_errors = np.sqrt(np.diag(pcov))
        A, p, B = popt

        num_randomized_qubits = num_qubits / 2
        dimension = 2**num_randomized_qubits
        epc = (dimension - 1) * (1 - p) / dimension
        epc_err = (dimension - 1) * param_errors[1] / dimension

        return {
            "fit_successful": True, "A": A, "p": p, "B": B,
            "epc": epc, "epc_err": epc_err,
            "params": tuple(popt), "param_errors": tuple(param_errors),
            "depths": depths, "mean_survivals": mean_survivals, "std_errors": std_errors
        }

    except (RuntimeError, ValueError):
        return _create_failure_result(depths, mean_survivals, std_errors)

def _create_failure_result(
    depths: Optional[np.ndarray] = None,
    mean_survivals: Optional[np.ndarray] = None,
    std_errors: Optional[np.ndarray] = None
) -> MRBFitResult:
    """Helper function to generate a dictionary for a failed fit."""
    nan_tuple = (np.nan, np.nan, np.nan)
    return {
        "fit_successful": False, "A": np.nan, "p": np.nan, "B": np.nan,
        "epc": np.nan, "epc_err": np.nan, "params": nan_tuple, "param_errors": nan_tuple,
        "depths": depths if depths is not None else np.array([]),
        "mean_survivals": mean_survivals if mean_survivals is not None else np.array([]),
        "std_errors": std_errors if std_errors is not None else np.array([])
    }

# --- Plotting Functions ---

def plot_mrb_decay(
    fit_result: MRBFitResult,
    qubit_group: Tuple[int, ...],
    save_dir: str
) -> None:
    """
    Plots the MRB survival probability decay and its exponential fit, saving it to a file.
    """
    if not _plotting_enabled:
        print("Warning: Plotting libraries (matplotlib, seaborn) not found. Skipping decay plot generation.")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    
    depths = fit_result['depths']
    mean_survivals = fit_result['mean_survivals']
    std_errors = fit_result['std_errors']

    ax.errorbar(
        depths, mean_survivals, yerr=std_errors,
        fmt='o', capsize=5, label='Experimental Data (Effective Polarization)', color='royalblue'
    )

    title_qubits = str(qubit_group)
    if fit_result["fit_successful"]:
        A, p, B = fit_result["params"]
        epc = fit_result["epc"]
        epc_err = fit_result["epc_err"]
        
        m_fit = np.linspace(min(depths), max(depths), 200)
        survival_fit = _mrb_decay_func(m_fit, A, p, B)
        
        label = (
            f'Exponential Fit\n'
            f'$p = {p:.4f} \\pm {fit_result["param_errors"][1]:.4f}$\n'
            f'EPC = ${epc:.2e} \\pm {epc_err:.2e}$'
        )
        ax.plot(m_fit, survival_fit, 'r-', label=label)
        ax.set_title(f'MRB Decay Curve for Qubits {title_qubits}')
    else:
        ax.set_title(f'MRB Decay Data for Qubits {title_qubits} (Fit Failed)')

    ax.set_xlabel('Clifford Sequence Depth (m)')
    ax.set_ylabel('Survival Probability (Effective Polarization)')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.legend(loc='best', fontsize='medium')
    
    os.makedirs(save_dir, exist_ok=True)
    qubit_str = '_'.join(map(str, qubit_group))
    save_path = os.path.join(save_dir, f'mrb_decay_qubits_{qubit_str}.png')
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close(fig)
    print(f"  -> Decay plot saved to: {save_path}")

def plot_scalability_heatmap(
    polarization_data: pd.DataFrame,
    save_path: str,
    title: str = 'MRB Scalability Heatmap'
) -> None:
    """
    Generates and saves a heatmap of effective polarization vs. number of qubits and circuit depth.
    """
    if not _plotting_enabled:
        print("Warning: Plotting libraries (matplotlib, seaborn) not found. Skipping heatmap generation.")
        return

    if not isinstance(polarization_data, pd.DataFrame) or polarization_data.empty:
        print("Error: polarization_data must be a non-empty Pandas DataFrame. Cannot generate heatmap.")
        return

    fig, ax = plt.subplots(figsize=(8, 10))
    sns.heatmap(
        polarization_data, ax=ax, annot=True, fmt=".4f",
        linewidths=.5, cmap="Blues",
        cbar_kws={'label': 'Mean Survival Probability (Effective Polarization)'}
    )
    ax.invert_yaxis()
    ax.set_title(title, fontsize=16, pad=20)
    ax.set_xlabel('Number of Qubits', fontsize=12)
    ax.set_ylabel('Circuit Depth', fontsize=12)
    
    save_dir = os.path.dirname(save_path)
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close(fig)
    print(f"  -> Scalability heatmap saved to: {save_path}")


# --- NEW HIGH-LEVEL FUNCTIONS ---

def display_mrb_summary(analysis_results: List[AnalysisResult]) -> None:
    """
    Displays a formatted summary table of MRB results in the console.

    Args:
        analysis_results: A list of AnalysisResult objects from an MRB experiment.
    """
    if not analysis_results:
        print("No analysis results to display.")
        return

    summary_data = []
    for res in analysis_results:
        metrics = res.data.get('metrics', {})
        summary_data.append({
            'Qubits': str(res.qubits),
            'Num Qubits': len(res.qubits),
            'EPC': metrics.get('EPC', np.nan),
            'EPC Error': metrics.get('EPC_err', np.nan),
            'Fit Success': res.data.get('fit_success', False)
        })
    
    results_df = pd.DataFrame(summary_data)
    print("\n--- Mirror RB Results Summary ---")
    print(results_df.to_string(index=False))

def generate_mrb_plots(analysis_results: List[AnalysisResult], output_dir: str) -> None:
    """
    Generates and saves all standard plots for an MRB experiment.

    This function creates:
    1. An individual decay curve plot for each qubit group.
    2. A scalability heatmap showing performance vs. qubit count and depth.

    Args:
        analysis_results: A list of AnalysisResult objects from an MRB experiment.
        output_dir: The directory where the plot files will be saved.
    """
    if not _plotting_enabled:
        print("Warning: Plotting libraries not installed. Skipping all plot generation.")
        return
    if not analysis_results:
        print("No analysis results to generate plots from.")
        return

    print("\nGenerating and saving plots...")

    # --- Plot 1: Individual decay curves for each qubit group ---
    for result in analysis_results:
        if "plot_data" in result.data:
            plot_mrb_decay(
                fit_result=result.data["plot_data"],
                qubit_group=tuple(result.qubits),
                save_dir=output_dir
            )

    # --- Plot 2: Scalability heatmap ---
    heatmap_points = [{
        "depth": depth,
        "num_qubits": len(result.qubits),
        "survival": np.mean(survivals)
    } for result in analysis_results
      for depth, survivals in result.data.get("raw_survival_data", {}).items()]

    if not heatmap_points:
        print("  -> Not enough data to generate the heatmap.")
        return

    try:
        heatmap_df = pd.DataFrame(heatmap_points).pivot(
            index='depth', columns='num_qubits', values='survival'
        ).sort_index().sort_index(axis=1)
        
        plot_scalability_heatmap(
            polarization_data=heatmap_df,
            save_path=os.path.join(output_dir, "mrb_scalability_heatmap.png")
        )
    except Exception as e:
        print(f"  -> Failed to generate heatmap: {e}")