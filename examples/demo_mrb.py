# File Path: examples/demo_mrb.py
# [DEMO ADAPTED for DummyBackend v1.2-clifford]

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
    print("   Mirror Randomized Benchmarking (MRB) Demonstration")
    print("   (Using DummyBackend with a single 'clifford_fidelity')")
    print("=" * 79)

    # --- 1. Framework Setup ---
    print("[INFO] Setting up a simulated backend and quantum engine...")
    
    # =========================================================================
    # [THE FIX IS HERE]
    # We now instantiate the backend using `clifford_fidelity` and `spam_error_rate`,
    # which are the parameters expected by your provided `dummy_backend.py`.
    #
    # IMPORTANT NOTE: This backend will apply the SAME fidelity (0.98) to both
    # the 1-qubit and 2-qubit circuits. The resulting analysis will show similar
    # EPC values for all qubit groups. This is a limitation of this specific
    # backend model for a multi-group MRB simulation.
    # =========================================================================
    backend = DummyBackend(
        clifford_fidelity=0.98, # Represents the fidelity of a Clifford operation (e.g., for the 2Q case)
        spam_error_rate=0.005
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
    # The mrb.py and rbleipzig.py files from my previous answers are robust
    # and DO NOT need to be changed. They work correctly with this setup.
    print("[STEP 2] Initializing and running the full MRB experiment workflow...")
    mrb_exp = MirrorRBExperiment(
        qubits=qubit_groups,
        depths=depths,
        circuits_per_depth=circuits_per_depth
    )
    
    # Create 'reports' directory if it doesn't exist
    report_dir = "reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    report_path = os.path.join(report_dir, "MRB_Report_Clifford_Fidelity_Model.xlsx")

    # The 'run' method handles everything.
    analysis_results = mrb_exp.run(
        engine, 
        shots=shots, 
        verbose=True, 
        report=True, 
        report_path=report_path
    )
    
    print("\n" + "=" * 79)
    print("MRB Demonstration finished successfully.")
    print(f"Check the console output and the generated report at: {report_path}")
    print("NOTE: The EPC for 1Q and 2Q groups will be similar due to the backend model used.")
    print("=" * 79)