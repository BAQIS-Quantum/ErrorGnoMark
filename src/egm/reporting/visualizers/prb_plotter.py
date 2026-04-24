# =============================================================================
# File: src/egm/reporting/visualizers/prb_plotter.py
# Version: v5.0 – Unified Purity RB Visualizer (EGM / XEB Style)
# Author : OpenAI‑Assistant
# =============================================================================
"""
Purity Randomized Benchmarking (PRB) Data Visualizer

Robust 2‑mode plot utility for visualizing calibrated Purity RB results.

Features
--------
✔ Calibrated display: (P − B)/A.
✔ Unified XEB color scheme (Blue / Orange).
✔ Comparison mode shows both std/interleaved decays + gate‑error.
✔ Fully compatible with EGM analysis layer.
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Dict, Any, Optional

# ---------------------------------------------------------------------
# Visual Style — Common with RB
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
})

COLOR = {
    "ref": "#1f77b4",        # Blue
    "int": "#d62728",        # Orange/Red
}

# ---------------------------------------------------------------------
# Single PRB Plot
# ---------------------------------------------------------------------
def plot_prb_single(
    results: Dict[str, Any],
    num_qubits: int,
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
) -> Axes:
    """Plot a single Purity RB decay (calibrated)."""
    if not results.get("fit_successful", False):
        print("[Warn] Skipping failed PRB fit visualization.")
        return ax or plt.gca()

    if ax is None:
        _, ax = plt.subplots(figsize=(6.2, 4.5))

    depths = np.array(results["depths"])
    y = np.array(results["calibrated_mean_purities"])
    yerr = np.array(results["calibrated_std_errors"])
    alpha = results.get("alpha", np.nan)

    ax.errorbar(
        depths,
        y,
        yerr=yerr,
        fmt="o",
        color=COLOR["ref"],
        ecolor=COLOR["ref"],
        capsize=4,
        label="Calibrated Purity Data",
    )

    if results.get("fit_successful"):
        fine = np.linspace(0, depths.max() if len(depths) else 1, 200)
        ax.plot(fine, alpha ** fine, "--", color="#ff7f0e", label=f"Fit (α={alpha:.4f})")

    ax.set_xlabel("Clifford Depth (m)")
    ax.set_ylabel("Calibrated Purity (P − B)/A")
    ax.set_title(title or f"Purity RB Decay ({num_qubits} Q)", fontweight="bold", pad=6)
    ax.set_ylim(-0.1, 1.05)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=False, loc="best")
    plt.tight_layout()
    return ax

# ---------------------------------------------------------------------
# Comparison Plot (Standard vs Interleaved)
# ---------------------------------------------------------------------
def plot_prb_comparison(
    results_std: Dict[str, Any],
    results_int: Dict[str, Any],
    num_qubits: int,
    target_gate_name: str,
    gate_error: Optional[float] = None,
    ax: Optional[Axes] = None,
) -> Axes:
    """Overlay Standard and Interleaved PRB fits and annotate gate error."""
    if ax is None:
        _, ax = plt.subplots(figsize=(6.4, 4.8))

    # Standard
    if results_std.get("fit_successful"):
        d_s = np.array(results_std["depths"])
        y_s = np.array(results_std["calibrated_mean_purities"])
        e_s = np.array(results_std["calibrated_std_errors"])
        a_s = results_std.get("alpha", np.nan)
        ax.errorbar(
            d_s, y_s, yerr=e_s, fmt="o", color=COLOR["ref"],
            ecolor=COLOR["ref"], capsize=4, label="Reference PRB"
        )
        fine = np.linspace(0, d_s.max() if len(d_s) else 1, 200)
        ax.plot(fine, a_s ** fine, "--", color=COLOR["ref"], label=f"α_std={a_s:.4f}")

    # Interleaved
    if results_int.get("fit_successful"):
        d_i = np.array(results_int["depths"])
        y_i = np.array(results_int["calibrated_mean_purities"])
        e_i = np.array(results_int["calibrated_std_errors"])
        a_i = results_int.get("alpha", np.nan)
        ax.errorbar(
            d_i, y_i, yerr=e_i, fmt="s", color=COLOR["int"],
            ecolor=COLOR["int"], capsize=4, label="Interleaved PRB"
        )
        fine2 = np.linspace(0, d_i.max() if len(d_i) else 1, 200)
        ax.plot(fine2, a_i ** fine2, "--", color=COLOR["int"], label=f"α_int={a_i:.4f}")

    # --- Gate Error Annotation ---
    if gate_error is not None and not np.isnan(gate_error):
        ax.text(
            0.03, 0.95, f"Gate Error = {gate_error:.2e}",
            transform=ax.transAxes,
            ha="left", va="top",
            fontsize=11.5,
            bbox=dict(boxstyle="round,pad=0.3",
                      facecolor="none", edgecolor="black", linewidth=0.6)
        )

    ax.set_xlabel("Clifford Depth (m)")
    ax.set_ylabel("Calibrated Purity (P − B)/A")
    ax.set_title(
        f"Interleaved PRB for '{target_gate_name.upper()}' ({num_qubits} Q)",
        fontweight="bold", pad=6,
    )
    ax.legend(frameon=False, loc="best")
    plt.tight_layout()
    return ax

# =============================================================================
# End of File
# =============================================================================