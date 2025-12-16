# File: errorgnomark/reporting/visualizers/rb_plotter.py
# ---------------------------------------------------------------------
# Module: Randomized Benchmarking (RB) Data Visualizer
# ---------------------------------------------------------------------
# Provides plotting functions for Standard and Interleaved RB analyses.
# Figures are rendered in a Nature/Science publication–style layout:
#   • Times New Roman serif font
#   • Subtle gray gridlines
#   • Colorblind‑friendly palette
#   • Clean legends and no background fills
#
# Integration:
#   - Used by automated HTML reports and end‑to‑end demos.
# ---------------------------------------------------------------------

from __future__ import annotations
from typing import Dict, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

# ---------------------------------------------------------------------
# Matplotlib Configuration (Nature/Science Aesthetic)
# ---------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "mathtext.fontset": "cm",
    "axes.linewidth": 1.0,
    "axes.labelsize": 15,
    "axes.titlesize": 15,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "legend.fontsize": 12,
    "grid.color": "#b0b0b0",
    "grid.linestyle": "-",
    "grid.linewidth": 0.6,
    "grid.alpha": 0.5,
    "axes.grid": True,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "xtick.direction": "in",
    "ytick.direction": "in",
})

# ---------------------------------------------------------------------
# Color Palette (Balanced, Colorblind Compatible)
# ---------------------------------------------------------------------
COLOR_PALETTE = {
    "data": "#0072B2",        # Oxford Blue
    "fit": "#D55E00",         # Burnt Orange
    "std": "#009E73",         # Emerald Green
    "interleaved": "#CC79A7", # Magenta
    "black": "#000000",
}

# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------
def _rb_decay_function(m: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """Exponential RB decay function f(m) = A * p^m + B."""
    return A * (p ** m) + B


# ---------------------------------------------------------------------
# Plot Single RB Dataset
# ---------------------------------------------------------------------
def plot_rb_data(
    results: Dict[str, Any],
    ax: Optional[Axes] = None,
    title: str = "Randomized Benchmarking",
    label: Optional[str] = None,
    color: Optional[str] = None,
    show_epc: bool = True,
) -> None:
    """
    Plot a single RB dataset (data + fit curve) using publication style.

    Args:
        results: Dictionary output from the RB fitting routine.
        ax: Optional Matplotlib Axes to draw on (creates new if None).
        title: Plot title.
        label: Legend label for the dataset.
        color: Optional custom color for the dataset points.
        show_epc: If True, annotate the calculated EPC in the figure corner.
    """
    if not results.get("fit_successful"):
        print(f"[Warning] Skipping failed fit plot for '{label or 'series'}'.")
        return

    if ax is None:
        _, ax = plt.subplots(figsize=(6.0, 4.2))

    depths = np.array(results["x_data"])
    probs = np.array(results["y_data"])
    errs = np.array(results["y_err"])
    params = results.get("params", {})

    color_data = color or COLOR_PALETTE["data"]
    color_fit = COLOR_PALETTE["fit"]

    # -----------------------------------------------------------------
    # Experimental Data Points
    # -----------------------------------------------------------------
    ax.errorbar(
        depths,
        probs,
        yerr=errs,
        fmt="o",
        markersize=5,
        mfc="white",
        mec=color_data,
        mew=1.2,
        ecolor=color_data,
        elinewidth=1,
        capthick=1,
        capsize=3,
        label=label or "Experimental Data",
    )

    # -----------------------------------------------------------------
    # Fit Curve
    # -----------------------------------------------------------------
    fit_depths = np.array(results.get("fit_x", []))
    fit_probs = np.array(results.get("fit_y", []))
    p = params.get("p", np.nan)

    if fit_depths.size and fit_probs.size:
        ax.plot(
            fit_depths,
            fit_probs,
            color=color_fit,
            linewidth=2.0,
            label=f"Fit (p = {p:.4f})",
        )

    # -----------------------------------------------------------------
    # Optional EPC Text Box
    # -----------------------------------------------------------------
    if show_epc and "epc" in results:
        ax.text(
            0.98,
            0.92,
            f"EPC = {results['epc']:.2e}",
            transform=ax.transAxes,
            fontsize=12.5,
            va="top",
            ha="right",
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="none",
                edgecolor="black",
                linewidth=0.7,
            ),
        )

    # -----------------------------------------------------------------
    # Axes and Formatting
    # -----------------------------------------------------------------
    ax.set_xlabel("Clifford Depth (m)")
    ax.set_ylabel("Ground‑State Survival Probability")
    ax.set_title(title, fontweight="bold", pad=6)
    ax.set_ylim(0.0, 1.05)
    ax.set_xlim(left=-max(depths) * 0.05)

    ax.grid(True, which="major", alpha=0.45, linewidth=0.6)
    ax.grid(True, which="minor", alpha=0.25, linewidth=0.4)
    ax.tick_params(top=True, right=True, width=1.0, length=4)

    for spine in ax.spines.values():
        spine.set_linewidth(1.0)

    ax.legend(frameon=False, loc="best")
    plt.tight_layout()


# ---------------------------------------------------------------------
# Plot Comparison (Standard vs Interleaved)
# ---------------------------------------------------------------------
def plot_rb_comparison(
    std_results: Dict[str, Any],
    interleaved_results: Dict[str, Any],
    target_gate_name: str,
    ax: Optional[Axes] = None,
) -> None:
    """
    Overlay two RB datasets (Standard and Interleaved) for comparison.

    Args:
        std_results: Fit dictionary for the Standard RB experiment.
        interleaved_results: Fit dictionary for the Interleaved RB experiment.
        target_gate_name: Name of the interleaved gate.
        ax: Optional Matplotlib Axes (creates new if None).
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(6.0, 4.2))

    # Plot standard RB
    plot_rb_data(
        std_results,
        ax=ax,
        label="Standard RB",
        color=COLOR_PALETTE["std"],
        show_epc=False,
    )

    # Plot interleaved RB
    plot_rb_data(
        interleaved_results,
        ax=ax,
        label=f"Interleaved RB ({target_gate_name})",
        color=COLOR_PALETTE["interleaved"],
        show_epc=False,
    )

    # -----------------------------------------------------------------
    # Annotation Box (Summary Text)
    # -----------------------------------------------------------------
    if std_results.get("epc") and interleaved_results.get("epg"):
        summary_text = (
            f"Reference EPC: {std_results['epc']:.3e}\n"
            f"Interleaved EPC: {interleaved_results['epc']:.3e}\n"
            f"Gate EPG ({target_gate_name}): {interleaved_results['epg']:.3e}"
        )
        ax.text(
            0.03,
            0.95,
            summary_text,
            transform=ax.transAxes,
            fontsize=12,
            va="top",
            ha="left",
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="none",
                edgecolor="black",
                linewidth=0.7,
            ),
        )

    # -----------------------------------------------------------------
    # Axes Finalization
    # -----------------------------------------------------------------
    ax.set_title(
        f"Interleaved RB Comparison for Gate '{target_gate_name}'",
        fontweight="bold",
        pad=6,
    )
    ax.tick_params(top=True, right=True, width=1.0, length=4)
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)

    ax.legend(frameon=False)
    plt.tight_layout()