# examples/demo_mrb.py

"""
This script demonstrates how to use the direct computation method for MRB.
This updated version uses the high-level `run_direct_analysis` method, which
automatically handles running the experiment, printing a summary table, and
generating a heatmap visualization of the results.
"""

import os
import sys
import numpy as np

# Add the project root to the Python path for imports
if '..' not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.mrb import MirrorRBExperiment

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================

CONFIG = {
    # The groups of qubits on which the experiment will be run.
    "qubit_groups": [0, 1, (0, 1), (0, 1, 2)],
    
    # The circuit depths for each MRB experiment.
    "depths": [10, 50, 100, 150, 200],
    
    # The number of random circuits to generate for each depth.
    "circuits_per_depth": 20,
    
    # The number of measurement shots for each circuit.
    "shots": 1024,
    
    # The error rate for the simulated backend.
    "depolarizing_error": 0.005,
    
    # --- [MODIFIED] ---
    # To display the plot interactively, set the save_path to None.
    # To save the plot to a file, provide a filename like "my_plot.png".
    "save_path": None
}

# ==============================================================================

def run_direct_mrb_analysis():
    """
    Main function to perform the direct MRB analysis.
    This function now uses the streamlined `run_direct_analysis` method.
    """
    # 1. Set up the simulated backend
    backend = DummyBackend(depolarizing_error=CONFIG["depolarizing_error"])
    print(f"\n[Setup] Using DummyBackend with depolarizing error = {CONFIG['depolarizing_error']}\n")

    # 2. Create the MRB experiment instance
    mrb_exp = MirrorRBExperiment(
        qubits=CONFIG["qubit_groups"],
        depths=CONFIG["depths"],
        circuits_per_depth=CONFIG["circuits_per_depth"]
    )
    
    # 3. Run the complete analysis with a single method call.
    # Because save_path is now None, this will cause the plot to be displayed.
    mrb_exp.run_direct_analysis(
        backend=backend,
        shots=CONFIG["shots"],
        verbose=True,
        save_path=CONFIG["save_path"]
    )

    # --- Interpretation of the results ---
    print("\n\n" + "=" * 60)
    print("    Interpretation of Results")
    print("=" * 60)
    print("\nThe summary table and the heatmap show the 'Effective Polarization (S)'.")
    print("This value is a measure of how well the quantum state survives the noisy circuit.")
    print("\nKey Takeaways:")
    print("  - Higher values (closer to 1.0) indicate better performance (less error).")
    print("  - Values decrease as 'Circuit Depth' increases, because longer circuits accumulate more noise.")
    print("  - Values for multi-qubit groups are typically lower than for single-qubit groups,")
    print("    reflecting the higher error rates of two-qubit gates.")


if __name__ == "__main__":
    run_direct_mrb_analysis()