# File Path: examples/demo_rb_final.py
# This script demonstrates the usage of the new, adapted RB experiment classes.
# It follows the user's specified demonstration flow.

import sys
import os
import matplotlib.pyplot as plt

# Ensure the main package is in the Python path
try:
    import errorgnomark
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from errorgnomark.engine import QuantumEngine
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.rb import StandardRBExperiment, InterleavedRBExperiment

print("=" * 70)
print("  Randomized Benchmarking (RB) Demonstration (Adapted Framework)")
print("=" * 70)
print("This demo showcases the RB experiments using the new BaseExperiment")
print("and QuantumEngine framework, following the user's specified logic.")
print("-" * 70 + "\n")


# --- Setup ---
# Use a dummy backend with some simulated noise
backend = DummyBackend(depolarizing_error_1q=0.002, depolarizing_error_2q=0.02, t_gate_error=0.005)
engine = QuantumEngine(backend=backend)


# =========================================================================
# Step 1: Generate and Display a Single Circuit
# =========================================================================
print("[Step 1] Generating a single 2-qubit INTERLEAVED RB circuit for inspection.")
# We create an experiment instance just to use its circuit generation method.
# We don't need to run the full experiment here.
demo_exp = InterleavedRBExperiment(
    qubits=[0, 1],
    target_gate_name='cnot',
    depths=[3], # We only need one depth
    circuits_per_depth=1
)
# Use the public method to generate one circuit
single_circuit = demo_exp.generate_single_circuit(depth=3, seed=42)
print("Generated a sample circuit with depth=3 and target gate 'cnot':")
print(single_circuit)
print("-" * 70 + "\n")


# =========================================================================
# Step 2: 1-Qubit Experiments
# =========================================================================
print("[Step 2] Performing 1-Qubit RB experiments...")

# --- 2.A: 1-Qubit Standard RB ---
print("\n[2.A] Running 1-Qubit Standard RB...")
std_exp_1q = StandardRBExperiment(
    qubits=[0],
    depths=[1, 10, 20, 40, 60, 80],
    circuits_per_depth=20
)
# Run the experiment and request a plot. The plot will be shown at the end.
std_results_1q = std_exp_1q.run(engine, shots=2048, plot=True)
print("1-Qubit Standard RB finished.")

# --- 2.B: 1-Qubit Interleaved RB ---
print("\n[2.B] Running 1-Qubit Interleaved RB for 'T' gate...")
int_exp_1q = InterleavedRBExperiment(
    qubits=[0],
    target_gate_name='t',
    depths=[1, 10, 20, 40, 60, 80],
    circuits_per_depth=20
)
# The run method handles everything: baseline, interleaved, analysis, and plotting.
full_results_1q = int_exp_1q.run(engine, shots=2048, plot=True)
print("1-Qubit Interleaved RB finished.")
print(f"  -> Calculated EPG for 'T' gate: {full_results_1q['gate_error']:.4e}")
print("-" * 70 + "\n")


# =========================================================================
# Step 3: 2-Qubit Experiments
# =========================================================================
print("[Step 3] Performing 2-Qubit RB experiments...")

# --- 3.A: 2-Qubit Standard RB ---
print("\n[3.A] Running 2-Qubit Standard RB...")
std_exp_2q = StandardRBExperiment(
    qubits=[0, 1],
    depths=[1, 5, 10, 15, 20],
    circuits_per_depth=15
)
std_results_2q = std_exp_2q.run(engine, shots=4096, plot=True)
print("2-Qubit Standard RB finished.")

# --- 3.B: 2-Qubit Interleaved RB ---
print("\n[3.B] Running 2-Qubit Interleaved RB for 'CNOT' gate...")
int_exp_2q = InterleavedRBExperiment(
    qubits=[0, 1],
    target_gate_name='cnot',
    depths=[1, 5, 10, 15, 20],
    circuits_per_depth=15
)
full_results_2q = int_exp_2q.run(engine, shots=4096, plot=True)
print("2-Qubit Interleaved RB finished.")
print(f"  -> Calculated EPG for 'CNOT' gate: {full_results_2q['gate_error']:.4e}")
print("-" * 70 + "\n")


# =========================================================================
# Final Step: Display All Generated Plots
# =========================================================================
print("Demonstration finished. All generated plots will now be displayed.")
print("Close ALL plot windows to exit the program.")
plt.show()