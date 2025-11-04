# File Path: examples/demo_spb.py
#
# [COMPATIBILITY UPDATE v3.1 - Aligned with DummyBackend v3.0]

import sys
import os
import matplotlib.pyplot as plt

# --- Python Path Setup ---
try:
    import errorgnomark
except ImportError:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# --- Framework Imports ---
from errorgnomark.engine.executor import QuantumEngine
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.spb import SPBExperiment, InterleavedSPBExperiment

if __name__ == "__main__":
    print("=" * 79)
    print("   Speckle Purity Benchmarking (SPB) Demonstration")
    print("=" * 79)

    # --- 1. Framework Setup ---
    # [FIX] Changed 'spam_error' to 'spam_error_rate' to match the new DummyBackend
    backend = DummyBackend(
        depolarizing_error_1q=0.001,
        depolarizing_error_2q=0.009,
        spam_error_rate=0.003
    )
    engine = QuantumEngine(backend=backend)
    print(f"Engine configured with '{backend.__class__.__name__}'")
    print("-" * 79 + "\n")

    # --- 2. One-Qubit SPB ---
    print("[STEP 1] Run 1-Qubit Standard and Interleaved SPB.")
    std_spb_1q_exp = SPBExperiment(qubits=[0], circuits_per_depth=25)
    # The plot flag will now correctly generate the plot internally
    results_std_1q = std_spb_1q_exp.run(engine, shots=4096, verbose=True, plot=True)
    
    int_spb_1q_exp = InterleavedSPBExperiment(qubits=[0], target_gate_name='H', circuits_per_depth=25)
    # The plot flag now generates the comparison plot
    int_spb_1q_exp.run(engine, shots=4096, standard_results=results_std_1q, verbose=True, plot=True)
    print("-" * 79 + "\n")

    # --- 3. Two-Qubit SPB ---
    print("[STEP 2] Run 2-Qubit Standard and Interleaved SPB.")
    std_spb_2q_exp = SPBExperiment(qubits=[0, 1], circuits_per_depth=20)
    results_std_2q = std_spb_2q_exp.run(engine, shots=4096, verbose=True, plot=True)
    
    int_spb_2q_exp = InterleavedSPBExperiment(qubits=[0, 1], target_gate_name='CNOT', circuits_per_depth=20)
    int_spb_2q_exp.run(engine, shots=4096, standard_results=results_std_2q, verbose=True, plot=True)
    print("-" * 79 + "\n")
    
    # --- 4. Final Message ---
    print("\nSPB Demonstration finished successfully.")
    print("[INFO] Displaying all generated plots. Please close plot windows to exit.")
    plt.show()
    print("=" * 79)