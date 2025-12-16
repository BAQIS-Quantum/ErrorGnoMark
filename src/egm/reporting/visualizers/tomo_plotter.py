# File Path: src/egm/reporting/visualizers/tomo_plotter.py
"""
Contains plotting functions for Tomography (QST/QPT) results.
"""

import itertools
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from egm.schemas.results.tomo import QSTAnalysisResult, QPTAnalysisResult

def plot_density_matrix(result: QSTAnalysisResult) -> Figure:
    """
    Generates 3D bar plots for the real and imaginary parts of a density matrix.

    Args:
        result: A QSTAnalysisResult object.

    Returns:
        A matplotlib Figure object of the plots.
    """
    rho = result.density_matrix
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError("Density matrix must be a square 2D array.")
    
    dim = rho.shape[0]
    title = f"QST Result (Qubits: {result.qubits}, Fidelity: {result.fidelity:.4f})"

    fig = plt.figure(figsize=(14, 6))
    fig.suptitle(title, fontsize=16)
    
    x, y = np.meshgrid(np.arange(dim), np.arange(dim))
    max_z = max(np.max(np.abs(rho)), 1e-12)

    # Real part
    ax_real = fig.add_subplot(1, 2, 1, projection="3d")
    ax_real.bar3d(x.ravel(), y.ravel(), 0, 0.8, 0.8, np.real(rho).ravel(), shade=True)
    ax_real.set_title("Real Part")
    ax_real.set_zlim(-max_z, max_z)

    # Imaginary part
    ax_imag = fig.add_subplot(1, 2, 2, projection="3d")
    ax_imag.bar3d(x.ravel(), y.ravel(), 0, 0.8, 0.8, np.imag(rho).ravel(), shade=True)
    ax_imag.set_title("Imaginary Part")
    ax_imag.set_zlim(-max_z, max_z)
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    return fig

def plot_chi_matrix(result: QPTAnalysisResult) -> Figure:
    """
    Generates heatmaps for the real and imaginary parts of a Chi process matrix.

    Args:
        result: A QPTAnalysisResult object.

    Returns:
        A matplotlib Figure object of the heatmaps.
    """
    chi = result.chi_matrix
    dim = chi.shape[0]
    n_qubits = len(result.qubits)
    labels = [''.join(p) for p in itertools.product('IXYZ', repeat=n_qubits)]
    title = f"QPT Result (Qubits: {result.qubits}, Fidelity: {result.process_fidelity:.4f})"
    
    real_part, imag_part = np.real(chi), np.imag(chi)
    vmax = np.max(np.abs(np.concatenate((real_part, imag_part))))
    
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(title, fontsize=16)

    for ax, matrix_part, part_name in zip(axs, [real_part, imag_part], ["Real", "Imaginary"]):
        im = ax.imshow(matrix_part, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        ax.set_xticks(range(dim))
        ax.set_yticks(range(dim))
        ax.set_xticklabels(labels, rotation=90)
        ax.set_yticklabels(labels)
        ax.set_title(f"{part_name} Part")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    return fig