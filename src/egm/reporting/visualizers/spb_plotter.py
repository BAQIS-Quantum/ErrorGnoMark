# =============================================================================
# File    : egm/reporting/visualizers/spb_plotter.py
# Version : v5.4 - Nature/Science Unified Edition (enhanced)
# Author  : OpenAI-Assistant
# =============================================================================
"""
State-Purity Benchmarking (SPB) Visualizer — Unified Layout
===========================================================

Nature/Science-style figure design, matched with RB and XEB v5.4 visuals.
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from typing import Any, Dict, Optional
from statistics import stdev

# -------------------------------------------------------------------------
# Global style configuration
# -------------------------------------------------------------------------
plt.rcParams.update(
    {
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
    }
)

COLOR = {
    "data": "#009E73",  # Emerald green
    "fit": "#E69F00",  # Golden orange
}


def _decay(x: np.ndarray, A: float, p: float, B: float) -> np.ndarray:
    """Exponential decay function f(x) = A * (p**x) + B."""
    return A * (p ** x) + B


def plot_spb_decay(
    raw_data: Dict[int, Any],
    fit_results: Optional[Dict[str, Any]] = None,
    ax: Optional[plt.Axes] = None,
    axis_mode: str = "depth",
    label: str = "SPB Data",
    color: str = COLOR["data"],
    error_bar_mode: str = "sem",
    show: bool = True,
) -> plt.Axes:
    """
    Publication-quality SPB decay plot consistent with RB/XEB visual standards.

    Parameters
    ----------
    raw_data : Dict[int, List[float]]
        Mapping depth or gate count to lists of purity values.
    fit_results : Optional[Dict]
        Fitted parameters including A, p_c, B, and optional std_errors.
    ax : Optional[plt.Axes]
        Existing matplotlib Axes on which to draw the plot.
    axis_mode : str
        "depth" or "gate_count" for x-axis labeling.
    label : str
        Label for raw data points.
    color : str
        Color for data markers.
    error_bar_mode : {"sem", "std"}
        Choose between standard error ("sem") or standard deviation ("std") bars.
    show : bool
        Whether to call plt.show() immediately.

    Returns
    -------
    matplotlib.axes.Axes
        The axis with the rendered figure.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(5.0, 3.6))
    if not raw_data:
        return ax

    x_vals = np.array(sorted(raw_data.keys()), float)
    means = np.array(
        [
            np.mean(raw_data[d]) if isinstance(raw_data[d], (list, np.ndarray)) else float(raw_data[d])
            for d in x_vals
        ]
    )

    # ------------------------------------------------------------------
    # Compute error bars
    # ------------------------------------------------------------------
    yerr_vals = []
    for idx, d in enumerate(x_vals):
        if isinstance(raw_data[d], (list, np.ndarray)):
            arr = np.asarray(raw_data[d], float)
            n = len(arr)
            if n > 1:
                if error_bar_mode.lower() == "std":
                    err = stdev(arr)
                else:
                    err = stdev(arr) / np.sqrt(n)
                yerr_vals.append(float(err))
            else:
                yerr_vals.append(0.0)
        elif fit_results and "std_errors" in fit_results:
            errs = fit_results["std_errors"]
            if isinstance(errs, dict):
                yerr_vals.append(float(errs.get(int(d), 0.0)))
            elif isinstance(errs, (list, tuple, np.ndarray)) and idx < len(errs):
                yerr_vals.append(float(errs[idx]))
            else:
                yerr_vals.append(0.0)
        else:
            yerr_vals.append(0.0)

    # Ensure visible error bars even for averaged points with zero variance
    if all(err == 0.0 for err in yerr_vals):
        yerr_vals = [0.002 for _ in yerr_vals]

    # ------------------------------------------------------------------
    # Plot data with error bars
    # ------------------------------------------------------------------
    ax.errorbar(
        x_vals,
        means,
        yerr=yerr_vals,
        fmt="o",
        mfc="white",
        mec=color,
        ecolor=color,
        mew=1.0,
        elinewidth=0.9,
        capsize=3,
        markersize=4.5,
        label=label,
    )

    # ------------------------------------------------------------------
    # Fitted exponential decay curve
    # ------------------------------------------------------------------
    if fit_results:
        A = float(fit_results.get("A", 0.0))
        p_c = float(
            fit_results.get(
                "p_c",
                fit_results.get(
                    "p_spb",
                    fit_results.get("p_fit", fit_results.get("p", 1.0)),
                ),
            )
        )
        B = float(fit_results.get("B", 0.0))

        fx = np.linspace(np.min(x_vals), np.max(x_vals), 250)
        fy = _decay(fx, A, p_c, B)
        ax.plot(
            fx,
            fy,
            "--",
            color=COLOR["fit"],
            lw=1.6,
            label=f"Fit (p_c={p_c:.4f})",
        )

    xlabel = "Total 1-Q Gate Count" if axis_mode.lower() == "gate_count" else "Circuit Depth"
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Mean State Purity")

    ax.set_ylim(0, min(1.05, float(np.max(means) * 1.2 + 0.05)))
    ax.set_title("State-Purity Benchmarking (SPB) Decay", fontweight="bold", pad=5)
    ax.legend(frameon=False, loc="lower right")

    for s in ax.spines.values():
        s.set_visible(True)
        s.set_linewidth(1.1)

    plt.tight_layout()
    if show:
        plt.show(block=True)
    return ax