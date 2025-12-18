# File: egm/reporting/visualizers/xeb_plotter.py
# ---------------------------------------------------------------------
# Module: Cross‑Entropy Benchmarking (XEB) + Speckle Purity Benchmarking (SPB)
# Visualizer
# ---------------------------------------------------------------------
# Provides plotting functions for Standard and Interleaved XEB analyses.
# Styling matches rb_plotter.py for publication diagrams.
# ---------------------------------------------------------------------

from __future__ import annotations
from typing import Dict, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

# ---------------------------------------------------------------------
# Matplotlib Aesthetics
# ---------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "mathtext.fontset": "cm",
    "axes.labelsize": 15,
    "axes.titlesize": 15,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "legend.fontsize": 12,
    "axes.grid": True,
    "grid.alpha": 0.5,
    "figure.dpi": 150,
})

COLOR_PALETTE = {
    "xeb_data": "#0072B2",
    "xeb_fit": "#D55E00",
    "spb_data": "#009E73",
    "spb_fit": "#CC79A7",
}

# ---------------------------------------------------------------------
# XEB plotting
# ---------------------------------------------------------------------
def plot_xeb_decay(
    raw_data: Dict[int, list],
    fit_results: Dict[str, float],
    ax: Optional[Axes] = None,
    label: str = "XEB Fidelity",
    color: Optional[str] = None,
) -> None:
    """Plot averaged XEB fidelity vs depth with exponential fit."""
    if ax is None:
        _, ax = plt.subplots(figsize=(6.0, 4.2))

    depths = np.array(sorted(raw_data.keys()))
    means = [np.mean(raw_data[d]) for d in depths]
    errs = [np.std(raw_data[d]) / np.sqrt(len(raw_data[d])) if len(raw_data[d]) > 1 else 0 for d in depths]

    color_pt = color or COLOR_PALETTE["xeb_data"]
    color_fit = COLOR_PALETTE["xeb_fit"]

    ax.errorbar(depths, means, yerr=errs, fmt="o", capsize=4, color=color_pt, label=label)
    if {"A","p","B"} <= fit_results.keys():
        fit_x = np.linspace(min(depths), max(depths), 200)
        fit_y = fit_results["A"] * (fit_results["p"] ** fit_x) + fit_results["B"]
        ax.plot(fit_x, fit_y, "--", color=color_fit, label=f"Fit (p={fit_results['p']:.4f})")

    ax.set_xlabel("Circuit Depth")
    ax.set_ylabel("XEB Fidelity")
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False)
    plt.tight_layout()


# ---------------------------------------------------------------------
# SPB plotting
# ---------------------------------------------------------------------
def plot_spb_decay(
    raw_data: Dict[int, list],
    fit_results: Dict[str, float],
    ax: Optional[Axes] = None,
    label: str = "Speckle Purity",
    color: Optional[str] = None,
) -> None:
    """Plot averaged SPB purity vs depth with fit."""
    if ax is None:
        _, ax = plt.subplots(figsize=(6.0, 4.2))

    depths = np.array(sorted(raw_data.keys()))
    means = [np.mean(raw_data[d]) for d in depths]
    errs = [np.std(raw_data[d]) / np.sqrt(len(raw_data[d])) if len(raw_data[d]) > 1 else 0 for d in depths]

    color_pt = color or COLOR_PALETTE["spb_data"]
    color_fit = COLOR_PALETTE["spb_fit"]

    ax.errorbar(depths, means, yerr=errs, fmt="o", capsize=4, color=color_pt, label=label)
    if {"A","p_c","B"} <= fit_results.keys():
        fit_x = np.linspace(min(depths), max(depths), 200)
        fit_y = fit_results["A"] * (fit_results["p_c"] ** fit_x) + fit_results["B"]
        ax.plot(fit_x, fit_y, "--", color=color_fit, label=f"Fit ($p_c$={fit_results['p_c']:.4f})")

    ax.set_xlabel("Circuit Depth")
    ax.set_ylabel("Speckle Purity")
    ax.legend(frameon=False)
    plt.tight_layout()