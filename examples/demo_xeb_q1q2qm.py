# File Path: examples/demo_xeb_professional.py
# [CORRECTED VERSION]
# This version correctly accesses the nested result dictionaries returned by the refactored experiment classes.

import sys
import os

# =========================================================================
# --- PLOTTING FIX: Force an Interactive Matplotlib Backend ---
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
from errorgnomark.experiments.benchmarking.xeb import StandardXEBExperiment, InterleavedXEBExperiment

# =========================================================================
# --- Main Demonstration Script ---
# =========================================================================

if __name__ == "__main__":

    print("=" * 79)
    print("      Professional Cross-Entropy Benchmarking (XEB) Demonstration")
    print("=" * 79)
    print("This demo relies on default parameters for maximal simplicity.")
    print("Parameter customization hints are in the source code comments.\n")

    # --- 1. Framework Setup ---
    print("[INFO] Setting up a simulated backend and quantum engine...")
    backend = DummyBackend(
        depolarizing_error_1q=0.003,
        depolarizing_error_2q=0.005,
    )
    engine = QuantumEngine(backend=backend)
    print(f"       Engine configured with '{backend.__class__.__name__}'")
    print(f"       Noise: 1Q Depolarizing = {backend.depolarizing_error_1q}, 2Q Depolarizing = {backend.depolarizing_error_2q}")
    print("-" * 79 + "\n")

    # --- 2. Generate and Display a Single Circuit ---
    print("[STEP 1] Generate a single, reproducible 2-Qubit Standard XEB circuit.")
    demo_exp_for_gen = StandardXEBExperiment(qubits=[0, 1], depths=[5])
    single_circuit = demo_exp_for_gen.generate_single_circuit(depth=5, seed=42)
    print("         Sample Circuit (depth=5, qubits=[0, 1]):")
    print(str(single_circuit))
    print("-" * 79 + "\n")

    # --- 3. One-Qubit Standard XEB ---
    print("[STEP 2] Run 1-Qubit Standard XEB to measure average cycle error.")
    std_exp_1q = StandardXEBExperiment(qubits=[0])
    results_1q = std_exp_1q.run(engine, shots=4096, plot=True, verbose=True)

    # [FIXED] Access the result via the correct nested path: ['fit_results']['error_per_cycle']
    epc_1q = results_1q['fit_results']['error_per_cycle']
    print(f"\n         > Result: Estimated 1Q EPC = {epc_1q:.6f}")
    
    print("Plotting 1Q Standard XEB results... Please close the plot window to continue.")
    plt.show()

    # --- 4. Two-Qubit Standard XEB (Baseline) ---
    print("\n[STEP 3] Run 2-Qubit Standard XEB to establish a baseline.")
    std_exp_2q = StandardXEBExperiment(qubits=[0, 1])
    results_2q_std = std_exp_2q.run(engine, shots=4096, plot=True, verbose=True)

    # [FIXED] Access the result via the correct nested path
    epc_2q = results_2q_std['fit_results']['error_per_cycle']
    print(f"\n         > Result: Estimated 2Q EPC = {epc_2q:.6f}")

    print("Plotting 2Q Standard XEB results... Please close the plot window to continue.")
    plt.show()

    # --- 5. Two-Qubit Interleaved XEB ---
    print("\n[STEP 4] Run 2-Qubit Interleaved XEB for 'cz' gate.")
    int_exp_2q = InterleavedXEBExperiment(qubits=[0, 1], target_gate_name='cz')
    results_2q_int = int_exp_2q.run(engine, shots=4096, plot=True, verbose=True)
    
    # [FIXED] Access the result via the correct nested path: ['gate_error_results']['error_per_gate']
    cz_error = results_2q_int['gate_error_results']['error_per_gate']
    print(f"\n         > Result: Estimated CZ Gate Error = {cz_error:.6f}")

    print("Plotting 2Q Interleaved XEB results... Please close the plot window to continue.")
    plt.show()

    # --- 6. Final Message ---
    print("\n" + "=" * 79)
    print("Demonstration finished successfully.")
    print("=" * 79)