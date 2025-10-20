# File Path: examples/demo_xeb_q1q2qm.py
# [ABSOLUTE FINAL VERSION - Correctly Reporting All Analysis Results]

import numpy as np
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from errorgnomark.engine import QuantumEngine
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.xeb import StandardXEBExperiment, InterleavedXEBExperiment
from errorgnomark.circuits.circuit import Gate

IBM_Q_NATIVE_GATES = {
    'id': 1, 'rz': 1, 'sx': 1, 'x': 1, 'cx': 2, 'reset': 1
}

# ================================================================================
# // SETUP: INITIALIZE THE ENGINE
# ================================================================================
backend = DummyBackend(cycle_fidelity=0.99, spam_error=0.0)
engine = QuantumEngine(backend)
print(f"Engine initialized with '{backend.name}' (Cycle Fidelity p = {backend.cycle_fidelity:.2f}). Expected EPC ≈ {1 - backend.cycle_fidelity:.3f}\n")


# ================================================================================
# // PART 1: CIRCUIT GENERATION & COMPILATION SHOWCASE
# ================================================================================
print("="*80)
print("// PART 1: CIRCUIT GENERATION & COMPILATION SHOWCASE")
print("="*80)
print("\nThis section demonstrates the core ability to generate and visualize logical")
print("circuits and compile them to different physical gate sets.\n")

# --- 1a. Generate a logical circuit ---
print(">>> 1a. Generating a logical 2-qubit XEB circuit...")
logical_exp = StandardXEBExperiment(qubits=[0, 1], gate_set="universal_xeb")
logical_circuit = logical_exp.generate_single_circuit(depth=2, native_gates=None)
print("Circuit diagram (logical gates, uncompiled):")
logical_circuit.draw()
print()

# --- 1b. Compile to different targets ---
print(">>> 1b. Compiling the logical circuit to different hardware targets...\n")

# Target 1: Default CZ-based gate set
print("--- Target 1: Default CZ-based gate set (e.g., Google Quantum AI) ---")
cz_basis_exp = StandardXEBExperiment(qubits=[0, 1], gate_set="universal_xeb")
cz_circuit = cz_basis_exp.generate_single_circuit(depth=2)
cz_circuit.draw()
print()

# Target 2: CNOT-based gate set
print("--- Target 2: Custom CNOT-based gate set (e.g., IBM Quantum) ---")
cnot_basis_exp = StandardXEBExperiment(qubits=[0, 1], gate_set="universal_xeb", native_gates=list(IBM_Q_NATIVE_GATES.keys()))
cnot_circuit = cnot_basis_exp.generate_single_circuit(depth=2)
cnot_circuit.draw()
print()

# --- 1c. Generate an Interleaved circuit ---
print(">>> 1c. Generating an Interleaved XEB circuit with a parameterized U3 gate...")
interleaved_gate = Gate('u3', (0,), params=[np.pi/2, np.pi/4, -np.pi/4])
interleaved_exp = InterleavedXEBExperiment(qubits=[0, 1], interleaved_gate=interleaved_gate, gate_set="universal_xeb")
interleaved_circuit = interleaved_exp.generate_single_circuit(depth=3, native_gates=None)
print(f"Circuit with '{interleaved_gate.name}' gate interleaved on qubit {interleaved_gate.qubits[0]}:")
interleaved_circuit.draw()
print()


# ================================================================================
# // PART 2: BULK CIRCUIT GENERATION FOR EXPERIMENTS
# ================================================================================
print("="*80)
print("// PART 2: BULK CIRCUIT GENERATION FOR EXPERIMENTS")
print("="*80)
print("\nThis demonstrates using the framework as a 'circuit generator' for large-scale")
print("experiments that might be run on external hardware or simulators.\n")

bulk_depths = [10, 20, 30, 40, 50]
circs_per_depth = 20
bulk_exp = StandardXEBExperiment(
    qubits=[0, 1, 2, 3],
    depths=bulk_depths,
    circuits_per_depth=circs_per_depth,
    gate_set="universal_xeb"
)
all_circuits = bulk_exp.circuits
print(f"SUCCESS: Generated a total of {len(all_circuits)} circuits for depths {bulk_depths}.")
print("These circuit objects can now be exported or executed elsewhere.\n")


# ================================================================================
# // PART 3: AUTOMATED END-TO-END EXPERIMENT
# ================================================================================
print("="*80)
print("// PART 3: AUTOMATED END-TO-END EXPERIMENT")
print("="*80)
print("\nThis shows the full, automated workflow: defining an experiment, running it,")
print("and automatically getting the final fitted benchmark result (EPC).\n")

print("Running automated XEB analysis on qubits [0, 1]...")
automated_exp = StandardXEBExperiment(
    qubits=[0, 1],
    depths=[2, 4, 6, 8, 10, 12, 14, 16],
    circuits_per_depth=15,
    gate_set="universal_xeb",
    seed=42
)

print("A plot window will appear. Please close it to continue the script.")
results = automated_exp.run(engine, shots=4096)

print("\n--- Analysis Complete ---")
epc = results['xeb_analysis']['fit_results']['epc']
print(f"Fitted Error Per Clifford (EPC) from XEB: {epc:.5f}")

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# [[[ THE FINAL, CORRECTED CODE ]]]
# The debug output showed the correct key is 'p_sq'. We now use it.
p_sq_val = results['spb_analysis']['fit_results']['p_sq']
print(f"Fitted Purity Decay Parameter (p²) from SPB: {p_sq_val:.5f}")
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

print("\n================================================================================")
print("DEMO COMPLETE: All stages executed successfully.")
print("================================================================================")