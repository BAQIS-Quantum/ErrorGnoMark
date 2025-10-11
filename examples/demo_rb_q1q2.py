# File Path: examples/demo_rb_professional.py
#
# ErrorGnomark: Professional Randomized Benchmarking Demonstration (Minimalist)
#
# This script showcases the core functionality of the RB experiments.
# It relies on default parameters but explicitly requests plotting, which is
# often an opt-in feature in professional libraries.

import sys
import os

# =========================================================================
# --- PLOTTING FIX: Force an Interactive Matplotlib Backend ---
# This ensures matplotlib attempts to create a GUI window for plots.
# This is good practice for scripts intended to be run from a terminal.
import matplotlib
matplotlib.use('TkAgg')
# =========================================================================

import matplotlib.pyplot as plt

# --- Python Path Setup ---
try:
    import errorgnomark
except ImportError:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)

# --- Framework Imports ---
from errorgnomark.engine import QuantumEngine
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.rb import StandardRBExperiment, InterleavedRBExperiment

# =========================================================================
# --- Main Demonstration Script ---
# =========================================================================

if __name__ == "__main__":

    print("=" * 79)
    print("      Professional Randomized Benchmarking (RB) Demonstration")
    print("=" * 79)
    print("This demo relies on default parameters for maximal simplicity.")
    print("Parameter customization hints are in the source code comments.\n")

    # --- 1. Framework Setup ---
    print("[INFO] Setting up a simulated backend and quantum engine...")
    backend = DummyBackend(
        depolarizing_error_1q=0.0018,
        depolarizing_error_2q=0.035,
        t_gate_error=0.002,
    )
    engine = QuantumEngine(backend=backend)
    print("-" * 79 + "\n")

    # --- 2. Generate and Display a Single Circuit ---
    print("[STEP 1] Generate a single, reproducible 2-Qubit Interleaved RB circuit.")
    demo_exp = InterleavedRBExperiment(qubits=[0, 1], target_gate_name='cnot')
    single_circuit = demo_exp.generate_single_circuit(depth=3, seed=42)
    print("         Sample Circuit (depth=3, target='cnot'):")
    print(str(single_circuit))
    print("-" * 79 + "\n")

    # --- 3. One-Qubit Standard RB ---
    print("[STEP 2] Run 1-Qubit Standard RB.")
    std_exp_1q = StandardRBExperiment(qubits=[0])
    # CORRECTED: Explicitly request plotting.
    std_exp_1q.run(engine, plot=True)
    print("Plotting 1Q Standard RB results... Please close the plot window to continue.")
    plt.show()

    # --- 4. One-Qubit Interleaved RB ---
    print("\n[STEP 3] Run 1-Qubit Interleaved RB for 't' gate.")
    int_exp_1q = InterleavedRBExperiment(qubits=[0], target_gate_name='t')
    # CORRECTED: Explicitly request plotting.
    int_exp_1q.run(engine, plot=True)
    print("Plotting 1Q Interleaved RB results... Please close the plot window to continue.")
    plt.show()

    # --- 5. Two-Qubit Standard RB ---
    print("\n[STEP 4] Run 2-Qubit Standard RB.")
    std_exp_2q = StandardRBExperiment(qubits=[0, 1])
    # CORRECTED: Explicitly request plotting.
    std_exp_2q.run(engine, plot=True)
    print("Plotting 2Q Standard RB results... Please close the plot window to continue.")
    plt.show()

    # --- 6. Two-Qubit Interleaved RB ---
    print("\n[STEP 5] Run 2-Qubit Interleaved RB for 'cnot' gate.")
    int_exp_2q = InterleavedRBExperiment(qubits=[0, 1], target_gate_name='cnot')
    # CORRECTED: Explicitly request plotting.
    int_exp_2q.run(engine, plot=True)
    print("Plotting 2Q Interleaved RB results... Please close the plot window to continue.")
    plt.show()

    # --- 7. Final Message ---
    print("\n" + "=" * 79)
    print("Demonstration finished successfully.")
    print("=" * 79)