# =============================================================================
# File: src/egm/reporting/visualizers/rb_plotter.py
# Version: v5.3 – Unified RB Visualizer (Full Border, PRB‑Matched Style)
# Author : OpenAI‑Assistant
# =============================================================================
"""
Randomized Benchmarking (RB) Data Visualizer

Description
-----------
Provides publication‑grade visualization for Standard and Interleaved RB results.
Matches the visual style of PRB (Purity RB) plots to ensure consistent appearance.

Key Features
-------------
- Serif fonts and fine gray grid (Nature/Science style)
- Color‑blind safe palette
- Unified dashed fit lines
- Consistent figure dimensions with PRB
- Full four‑side borders
- Backward‑compatible with previous v5.x interfaces
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Dict, Any, Optional

# ---------------------------------------------------------------------
# Global Configuration
# ---------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "cm",
    "axes.linewidth": 1.1,
    "axes.labelsize": 14,
    "axes.titlesize": 14,
    "xtick.labelsize": 12.5,
    "ytick.labelsize": 12.5,
    "legend.fontsize": 11,
    "grid.color": "#c0c0c0",
    "grid.linestyle": "--",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.35,
    "axes.grid": True,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "axes.spines.top": True,
    "axes.spines.right": True,
})

# ---------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------
COLOR = {
    "data": "#0072B2",        # Oxford blue
    "fit": "#E69F00",         # Golden orange
    "std": "#009E73",         # Emerald green
    "interleaved": "#D55E00", # Burnt orange
}


# ---------------------------------------------------------------------
# Helper Function
# ---------------------------------------------------------------------
def _decay(m: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """Exponential RB decay function: f(m) = A * p^m + B."""
    return A * (p ** m) + B


# ---------------------------------------------------------------------
# Plot a Single RB Decay
# ---------------------------------------------------------------------
def plot_rb_data(
    results: Dict[str, Any],
    ax: Optional[Axes] = None,
    title: str = "Randomized Benchmarking",
    x_axis_mode: str = "gate_count",
    label: Optional[str] = None,
    color: Optional[str] = None,
    show_epc: bool = True,
) -> Axes:
    """
    Render a single RB dataset in publication‑style.

    Parameters
    ----------
    results : dict
        Dictionary containing RB results and fit parameters.
    ax : matplotlib.axes.Axes, optional
        Existing axis to draw on.
    title : str
        Figure title.
    x_axis_mode : str
        "depth" or "gate_count" to choose x‑axis scaling.
    label : str, optional
        Legend label.
    color : str, optional
        Color override for data points.
    show_epc : bool
        Whether to display the extracted EPC value.

    Returns
    -------
    matplotlib.axes.Axes
        The axis object with the rendered plot.
    """
    if not results.get("fit_successful", False):
        print(f"[Warn] Fit unsuccessful, skipping plot for {label or 'dataset'}.")
        return ax or plt.gca()

    if ax is None:
        _, ax = plt.subplots(figsize=(5.0, 3.6))  # unified with PRB

    depths = np.array(results.get("depths", []))
    gates = np.array(results.get("gate_counts", []))
    means = np.array(results.get("means", []))
    errs = np.array(results.get("std_errors", []))
    A, B, p = results.get("A"), results.get("B"), results.get("p")

    x_vals, xlabel = depths, "Clifford Depth (m)"
    if x_axis_mode.lower() == "gate_count" and not np.all(np.isnan(gates)):
        x_vals = gates
        xlabel = "Total Gate Count"

    c_data = color or COLOR["data"]
    c_fit = COLOR["fit"]

    # Plot data points with error bars
    ax.errorbar(
        x_vals, means, yerr=errs,
        fmt="o", mfc="white", mec=c_data, mew=1.0,
        ecolor=c_data, elinewidth=0.8, capsize=3,
        markersize=4.5, label=label or "RB Data",
    )

    # Fit curve (dashed line, unified with PRB)
    fit_x = np.linspace(np.min(depths), np.max(depths), 250)
    fit_y = _decay(fit_x, A, p, B)
    if x_axis_mode.lower() == "gate_count" and not np.all(np.isnan(gates)):
        from scipy.interpolate import interp1d
        valid = ~np.isnan(gates)
        fit_x_plot = interp1d(depths[valid], gates[valid], fill_value="extrapolate")(fit_x)
    else:
        fit_x_plot = fit_x
    ax.plot(fit_x_plot, fit_y, "--", color=c_fit, lw=1.6, label=f"Fit (p={p:.4f})")

    # Add EPC annotation
    if show_epc and "epc" in results:
        ax.text(
            0.97, 0.93,
            f"EPC = {results['epc']:.2e}",
            transform=ax.transAxes,
            fontsize=11,
            va="top", ha="right",
            color="#202020",
            bbox=dict(boxstyle="round,pad=0.25",
                      facecolor="white",
                      edgecolor="#808080",
                      linewidth=0.6),
        )

    # Axis formatting
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Ground‑State Survival Probability")
    ax.set_title(title, fontweight="bold", pad=5)
    ax.set_ylim(0, 1.05)
    ax.tick_params(width=1.0, length=4)

    # Ensure all four spines are visible and styled uniformly
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.1)

    ax.legend(frameon=False, loc="lower right")
    plt.tight_layout()
    return ax


# ---------------------------------------------------------------------
# Plot Standard vs. Interleaved RB Comparison
# ---------------------------------------------------------------------
def plot_rb_comparison(
    results_std: Dict[str, Any],
    results_int: Dict[str, Any],
    num_qubits: int,
    target_gate_name: str,
    ax: Optional[Axes] = None,
    x_axis_mode: str = "gate_count",
) -> Axes:
    """
    Overlay two RB datasets (Standard and Interleaved) for comparison.

    Parameters
    ----------
    results_std : dict
        Standard RB results.
    results_int : dict
        Interleaved RB results.
    num_qubits : int
        Number of qubits involved.
    target_gate_name : str
        Name of the interleaved gate.
    ax : matplotlib.axes.Axes, optional
        Existing axis.
    x_axis_mode : str
        "depth" or "gate_count".

    Returns
    -------
    matplotlib.axes.Axes
        The axis object with the rendered plot.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(5.0, 3.6))

    plot_rb_data(
        results_std,
        ax=ax,
        title="",
        x_axis_mode=x_axis_mode,
        label="Standard RB",
        color=COLOR["std"],
        show_epc=False,
    )

    plot_rb_data(
        results_int,
        ax=ax,
        title="",
        x_axis_mode=x_axis_mode,
        label="Interleaved RB",
        color=COLOR["interleaved"],
        show_epc=False,
    )

    epc_ref = results_std.get("epc", np.nan)
    epc_int = results_int.get("epc", np.nan)
    epg = results_int.get("epg", np.nan)

    summary = (
        f"Reference EPC: {epc_ref:.3e}\n"
        f"Interleaved EPC: {epc_int:.3e}\n"
        f"Gate EPG ({target_gate_name}): {epg:.3e}"
    )
    ax.text(
        0.03, 0.95,
        summary,
        transform=ax.transAxes,
        fontsize=11,
        va="top", ha="left",
        color="#202020",
        bbox=dict(boxstyle="round,pad=0.25",
                  facecolor="white",
                  edgecolor="#808080",
                  linewidth=0.6),
    )

    ax.set_title(
        f"Interleaved RB for '{target_gate_name}' ({num_qubits}Q)",
        fontweight="bold",
        pad=5,
    )
    ax.set_xlabel("Clifford Depth / Gate Count")
    ax.set_ylabel("Ground‑State Survival Probability")

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.1)

    ax.legend(frameon=False, loc="lower right")
    plt.tight_layout()
    return ax


# =============================================================================
# End of File
# =============================================================================