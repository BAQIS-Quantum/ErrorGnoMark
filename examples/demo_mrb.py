# File Path: examples/demo_mrb.py
# [UPDATED DEMO - To match the adapted MRB experiment class]

import sys
import os
import matplotlib
matplotlib.use('TkAgg')

# --- Python Path Setup ---
try:
    import errorgnomark
except ImportError:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path: sys.path.insert(0, project_root)

# --- Framework Imports ---
from errorgnomark.engine import QuantumEngine
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.mrb import MirrorRBExperiment

if __name__ == "__main__":
    print("=" * 79)
    print("   Mirror Randomized Benchmarking (MRB) Demonstration (Adapted Workflow)")
    print("=" * 79)

    # --- 1. Framework Setup ---
    print("[INFO] Setting up a simulated backend and quantum engine...")
    backend = DummyBackend(
        depolarizing_error_1q=0.001,
        depolarizing_error_2q=0.01,
        spam_error=0.005
    )
    engine = QuantumEngine(backend=backend)
    print("-" * 79 + "\n")

    # --- 2. Define the Experiment Parameters ---
    print("[STEP 1] Defining the MRB experiment parameters.")
    qubit_groups = [0, 1, (0, 1)] # 1Q on Q0, 1Q on Q1, 2Q on Q0-Q1
    depths = [1, 10, 20, 50, 80, 120]
    circuits_per_depth = 20
    shots = 2048
    
    print(f"  Qubit Groups: {qubit_groups}")
    print(f"  Depths: {depths}")
    print(f"  Circuits per Depth: {circuits_per_depth}")
    print(f"  Shots per Circuit: {shots}")
    print("-" * 79 + "\n")
    
    # --- 3. Initialize and Run the Experiment ---
    print("[STEP 2] Initializing and running the full MRB experiment workflow...")
    mrb_exp = MirrorRBExperiment(
        qubits=qubit_groups,
        depths=depths,
        circuits_per_depth=circuits_per_depth
    )
    
    # The 'run' method now handles everything: execution, analysis, and reporting.
    # The final analysis results are returned.
    analysis_results = mrb_exp.run(
        engine, 
        shots=shots, 
        verbose=True, 
        report=True, 
        report_path="MRB_Report_Adapted.xlsx"
    )
    
    print("\n" + "=" * 79)
    print("MRB Demonstration finished successfully.")
    print(f"Check the console output and the generated report at: reports/MRB_Report_Adapted.xlsx")
    print("=" * 79)