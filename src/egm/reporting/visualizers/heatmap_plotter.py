# File Path: src/egm/reporting/visualizers/heatmap_plotter.py
"""
Contains the plotting function for MRB polarization heatmaps.
This is a specific type of plot often used in multi-qubit RB variants.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Note: For MRB, you would create a dedicated MRBAnalysisResult schema
# that inherits from RBAnalysisResult and adds these fields.
# For now, we'll assume they might exist on a generic RBAnalysisResult.
from egm.schemas.results.rb import RBAnalysisResult 

def plot_mrb_heatmap(result: RBAnalysisResult) -> Figure:
    """
    Generates an MRB polarization heatmap.
    
    This function expects MRB-specific fields ('avg_polarizations', 'qubit_groups')
    to be present in the result object.

    Args:
        result: An analysis result object, expected to contain MRB data.

    Returns:
        A matplotlib Figure object of the heatmap.
    """
    # These attributes are not on the base RB schema, so we use getattr
    polarizations = getattr(result, 'avg_polarizations', None)
    groups = getattr(result, 'qubit_groups', None)
    depths = [dp.sequence_length for dp in result.sequence_data]

    if polarizations is None or not groups:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No MRB heatmap data available.", ha='center', va='center')
        return fig

    pol_array = np.array(polarizations)
    
    fig, ax = plt.subplots(figsize=(
        max(8, len(groups) * 1.5), 
        max(5, len(depths) * 0.6)
    ))
    
    im = ax.imshow(pol_array.T, cmap="Blues", vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([str(g) for g in groups], rotation=45, ha="right")
    ax.set_yticks(range(len(depths)))
    ax.set_yticklabels(depths)
    
    ax.set_xlabel("Qubit Groups")
    ax.set_ylabel("Clifford Depth (m)")
    ax.set_title("MRB Direct Polarization Heatmap", pad=20)

    # Add text annotations
    for i in range(pol_array.shape[0]):      # iterating over depths
        for j in range(pol_array.shape[1]):  # iterating over groups
            val = pol_array[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    color="white" if val > 0.5 else "black", fontsize=8)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.2)
    fig.colorbar(im, cax=cax, label="Effective Polarization")
    
    plt.tight_layout()
    return fig