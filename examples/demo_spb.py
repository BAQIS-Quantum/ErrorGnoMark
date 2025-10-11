# File Path: examples/demo_spb.py
#
# ErrorGnomark: Speckle Purity Benchmarking (SPB) Demonstration

import sys
import os
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# --- Python Path Setup ---
try:
    import errorgnomark
except ImportError:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# --- Framework Imports ---
from errorgnomark.engine import QuantumEngine
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.spb import SPBExperiment, InterleavedSPBExperiment

if __name__ == "__main__":
    print("=" * 79)
    print("   Speckle Purity Benchmarking (SPB) Demonstration")
    print("=" * 79)
    print("This demo uses default parameters for simplicity.\n")

    # --- 1. Framework Setup ---
    print("[INFO] Setting up a simulated backend and quantum engine...")
    backend = DummyBackend(
        depolarizing_error_1q=0.001,
        depolarizing_error_2q=0.009,
        spam_error=0.003
    )
    engine = QuantumEngine(backend=backend)
    print(f"       Engine configured with '{backend.__class__.__name__}'")
    print(f"       Noise: 1Q Depolarizing = {backend.depolarizing_error_1q}, 2Q Depolarizing = {backend.depolarizing_error_2q}")
    print("-" * 79 + "\n")

    # --- 2. Generate and Display a Sample Circuit ---
    print("[STEP 1] Generate a single, reproducible 1-Qubit SPB circuit.")
    # Note: SPB circuits do not have an inverse layer.
    demo_exp = SPBExperiment(qubits=[0], depths=[5])
    sample_circuit = demo_exp.circuits[0]
    print("         Sample Circuit (depth=5):")
    print(str(sample_circuit))
    print("-" * 79 + "\n")

    # --- 3. One-Qubit Standard SPB ---
    print("[STEP 2] Run 1-Qubit Standard SPB.")
    std_spb_1q = SPBExperiment(qubits=[0], circuits_per_depth=25, depths=list(range(5, 101, 10)))
    std_spb_1q.run(engine, shots=4096, verbose=True, plot=True)
    print("Plotting 1Q Standard SPB results... Please close the plot window to continue.")
    
    # --- 4. One-Qubit Interleaved SPB ---
    print("\n[STEP 3] Run 1-Qubit Interleaved SPB for 'H' (Hadamard) gate.")
    int_spb_1q = InterleavedSPBExperiment(qubits=[0], target_gate_name='H', circuits_per_depth=25, depths=list(range(5, 101, 10)))
    int_spb_1q.run(engine, shots=4096, verbose=True, plot=True)
    print("Plotting 1Q Interleaved SPB results... Please close the plot window to continue.")
    
    # --- 5. Two-Qubit Standard SPB ---
    print("\n[STEP 4] Run 2-Qubit Standard SPB.")
    std_spb_2q = SPBExperiment(qubits=[0, 1], circuits_per_depth=20, depths=list(range(4, 41, 4)))
    std_spb_2q.run(engine, shots=4096, verbose=True, plot=True)
    print("Plotting 2Q Standard SPB results... Please close the plot window to continue.")
    
    # --- 6. Two-Qubit Interleaved SPB ---
    print("\n[STEP 5] Run 2-Qubit Interleaved SPB for 'CNOT' gate.")
    int_spb_2q = InterleavedSPBExperiment(qubits=[0, 1], target_gate_name='CNOT', circuits_per_depth=20, depths=list(range(4, 41, 4)))
    int_spb_2q.run(engine, shots=4096, verbose=True, plot=True)
    print("Plotting 2Q Interleaved SPB results... Please close the plot window to continue.")
    
    # --- 7. Final Message ---
    print("\n" + "=" * 79)
    print("SPB Demonstration finished successfully.")
    print("=" * 79)