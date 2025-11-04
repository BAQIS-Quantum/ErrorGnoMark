# File Path: examples/demo_mrb.py
# [DEFINITIVE FINAL VERSION v8 - Ultimate Simplicity]

import sys
import os

# --- Dynamic Path Setup ---
# Allows the script to find the 'errorgnomark' package from the 'examples' directory.
try:
    import errorgnomark
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Core Library Imports ---
from errorgnomark.experiments.benchmarking.mrb import MirrorRBExperiment
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.engine.executor import QuantumEngine
# Import the NEW high-level analysis functions
from errorgnomark.analysis.mrb import display_mrb_summary, generate_mrb_plots


if __name__ == "__main__":
    # --- 1. Basic Setup ---
    # All results will be saved here.
    output_dir = "results/mrb_demo_ultimate"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Running Ultimate Simplicity MRB Demo. Results will be saved in '{os.path.abspath(output_dir)}'")

    # Define the backend, experiment parameters, and the experiment itself.
    backend = DummyBackend(depolarizing_error_1q=1e-3, depolarizing_error_2q=1e-2, seed=42)
    
    qubit_groups = [
        (0, 1),               # 2 qubits
        (2, 3, 4, 5),         # 4 qubits
        (6, 7, 8, 9, 10, 11), # 6 qubits
    ]
    
    experiment = MirrorRBExperiment(
        qubits=qubit_groups,
        depths=[4, 8, 16, 32, 64],
        circuits_per_depth=25,
        seed=123
    )

    # --- 2. Run Experiment ---
    # The engine executes the experiment circuits on the backend.
    # The `run` method automatically handles circuit generation, execution, and analysis.
    print("Running experiment... (This may take a moment)")
    engine = QuantumEngine(backend=backend)
    analysis_results = experiment.run(engine, shots=1024)
    print("Experiment finished.")

    # --- 3. Display Summary & Generate All Plots ---
    # These new high-level functions encapsulate all post-processing, table generation, and plotting.
    # The demo script is now clean and focuses only on running the experiment.
    
    # Call a single function to display the results table.
    display_mrb_summary(analysis_results)
    
    # Call a single function to generate and save all plots.
    generate_mrb_plots(analysis_results, output_dir=output_dir)
    
    print("\nDemo complete.")