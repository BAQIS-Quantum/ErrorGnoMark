# File Path: examples/demo_prb.py
# [FINAL VERSION - Uses correct gate name 'CNOT' and aligned with new modules]

import sys
import os
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

try:
    import errorgnomark
except ImportError:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from errorgnomark.engine import QuantumEngine
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.prb import StandardPRBExperiment, InterleavedPRBExperiment

if __name__ == "__main__":
    print("=" * 79)
    print("   Professional Purity Randomized Benchmarking (PRB) Demonstration")
    print("=" * 79)
    print("This demo relies on default parameters for maximal simplicity.\n")

    print("[INFO] Setting up a simulated backend and quantum engine...")
    backend = DummyBackend(
        depolarizing_error_1q=0.002,
        depolarizing_error_2q=0.015,
        spam_error=0.005
    )
    engine = QuantumEngine(backend=backend)
    print(f"       Engine configured with '{backend.__class__.__name__}'")
    print(f"       Noise: 1Q Depolarizing = {backend.depolarizing_error_1q}, 2Q Depolarizing = {backend.depolarizing_error_2q}")
    print("-" * 79 + "\n")

    print("[STEP 1] Generate a single, reproducible 1-Qubit PRB circuit pair.")
    demo_exp = StandardPRBExperiment(qubits=[0])
    circuit_a, circuit_b = demo_exp._generate_circuit_pair(depth=3, seed=123)
    print("         Sample Circuit A (with Pauli Twirl, depth=3):")
    print(str(circuit_a))
    print("\n         Sample Circuit B (without Pauli Twirl, depth=3):")
    print(str(circuit_b))
    print("-" * 79 + "\n")

    print("[STEP 2] Run 1-Qubit Standard PRB.")
    std_prb_1q = StandardPRBExperiment(qubits=[0], circuits_per_depth=25)
    std_prb_1q.run(engine, shots=4096, verbose=True, plot=True)
    print("Plotting 1Q Standard PRB results... Please close the plot window to continue.")
    plt.show()

    print("\n[STEP 3] Run 1-Qubit Interleaved PRB for 'H' (Hadamard) gate.")
    int_prb_1q = InterleavedPRBExperiment(qubits=[0], target_gate_name='H', circuits_per_depth=25)
    int_prb_1q.run(engine, shots=4096, verbose=True, plot=True)
    print("Plotting 1Q Interleaved PRB results... Please close the plot window to continue.")
    plt.show()

    print("\n[STEP 4] Run 2-Qubit Standard PRB.")
    std_prb_2q = StandardPRBExperiment(qubits=[0, 1], circuits_per_depth=20)
    std_prb_2q.run(engine, shots=4096, verbose=True, plot=True)
    print("Plotting 2Q Standard PRB results... Please close the plot window to continue.")
    plt.show()

    print("\n[STEP 5] Run 2-Qubit Interleaved PRB for 'CNOT' gate.")
    # [THE FIX] Using 'CNOT' (uppercase) as it is a more common standard name in backends.
    int_prb_2q = InterleavedPRBExperiment(qubits=[0, 1], target_gate_name='CNOT', circuits_per_depth=20)
    int_prb_2q.run(engine, shots=4096, verbose=True, plot=True)
    print("Plotting 2Q Interleaved RB results... Please close the plot window to continue.")
    plt.show()

    print("\n" + "=" * 79)
    print("Demonstration finished successfully.")
    print("=" * 79)