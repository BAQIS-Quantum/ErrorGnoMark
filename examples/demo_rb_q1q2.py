# File Path: examples/demo_rb_q1q2.py
# CORRECTED to import and instantiate the DummyBackend.

# --- [FIX 1/2] Import necessary classes ---
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.rb import StandardRBExperiment, InterleavedRBExperiment

# --- [FIX 2/2] Create an instance of the backend ---
# We instantiate the backend here, providing some example error rates.
# 0.1% depolarizing error and 0.2% SPAM error.
backend = DummyBackend(depolarizing_error=0.015, spam_error=0.0001)

print("="*50)
print("      Randomized Benchmarking (RB) Demonstration")
print("="*50)
print("[Setup] Using a simulated backend with depolarizing and SPAM error.\n")


# --- Example 1: Standard 1-Qubit RB ---
print("="*20, "Standard 1-Qubit RB", "="*20)
std_rb_1q = StandardRBExperiment(qubits=[0], circuits_per_depth=20)
std_results_1q = std_rb_1q.run_and_fit(backend, verbose=True, plot=True)
print(f"Final Result: 1Q EPC = {std_results_1q.get('epc', -1):.3e}")


# --- Example 2: Interleaved 1-Qubit RB for 'H' gate ---
print("\n" + "="*20, "Interleaved 1-Qubit RB ('H')", "="*20)
int_rb_h = InterleavedRBExperiment(qubits=[0], target_gate_name='H', circuits_per_depth=20)
int_results_h = int_rb_h.run_and_fit(backend, verbose=True, plot=True)
print(f"Final Result: Error of 'H' gate = {int_results_h.get('gate_error', -1):.3e}")


# --- Example 3: Standard 2-Qubit RB ---
print("\n" + "="*20, "Standard 2-Qubit RB", "="*20)
std_rb_2q = StandardRBExperiment(qubits=[0, 1], circuits_per_depth=20)
std_results_2q = std_rb_2q.run_and_fit(backend, verbose=True, plot=True)
print(f"Final Result: 2Q EPC = {std_results_2q.get('epc', -1):.3e}")


# --- Example 4: Interleaved 2-Qubit RB for 'CNOT' gate ---
print("\n" + "="*20, "Interleaved 2-Qubit RB ('CNOT')", "="*20)
int_rb_cnot = InterleavedRBExperiment(qubits=[0, 1], target_gate_name='CNOT', circuits_per_depth=20)
int_results_cnot = int_rb_cnot.run_and_fit(backend, verbose=True, plot=True)
print(f"Final Result: Error of 'CNOT' gate = {int_results_cnot.get('gate_error', -1):.3e}")

print("\n" + "="*50)
print("Demonstration complete!")
print("="*50)