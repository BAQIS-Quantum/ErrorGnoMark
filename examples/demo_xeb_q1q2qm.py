# # File Path: examples/demo_xeb_custom_gates.py
# [REFACTORED VERSION 4 - Using the custom native gate set from the user's image]

import numpy as np
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from errorgnomark.engine import QuantumEngine
from errorgnomark.backends.dummy_backend_xeb import DummyBackend
from errorgnomark.experiments.benchmarking.xeb import StandardXEBExperiment, InterleavedXEBExperiment
from errorgnomark.circuits.circuit import Gate

# ================================================================================
# // DEFINING THE NATIVE GATE SET FROM THE PROVIDED IMAGE
# ================================================================================
# This gate set is based on the gates provided in the user's image.
# We use standard names that the framework's compiler understands:
# - 'sx' corresponds to the X/2 or Rx(pi/2) gate.
# - 'rz' represents arbitrary Z-rotations, which can be constructed from S and T gates.
# - 'cz' is the Controlled-Z gate, which is explicitly listed.
# - 'id' is the identity gate.
# This forms a universal gate set.
CUSTOM_NATIVE_GATES = {
    'id': 1, 
    'sx': 1, 
    'rz': 1, 
    'cz': 2
}

# ================================================================================
# // SETUP: INITIALIZE THE ENGINE
# ================================================================================
# NOTE: The parameters for DummyBackend are explicitly specified.
backend = DummyBackend(cycle_fidelity=0.999, spam_error=0.0001)
engine = QuantumEngine(backend)
print(f"Engine initialized with '{backend.name}' (Cycle Fidelity p = {backend.cycle_fidelity:.2f}). Expected EPC ≈ {1 - backend.cycle_fidelity:.3f}\n")


# ================================================================================
# // PART 1: CIRCUIT GENERATION & COMPILATION SHOWCASE
# ================================================================================
print("="*80)
print("// PART 1: CIRCUIT GENERATION & COMPILATION SHOWCASE")
print("="*80)
print("\nThis section demonstrates generating a logical circuit and compiling it")
print("to the custom native gate set derived from your provided image.\n")

# --- 1a. Generate a logical circuit ---
print(">>> 1a. Generating a logical 2-qubit XEB circuit (using abstract fSim gates)...")
# The default gate_set="universal_xeb" uses fSim gates, which are logical/abstract.
logical_exp = StandardXEBExperiment(qubits=[0, 1])
logical_circuit = logical_exp.generate_single_circuit(depth=2, seed=1) # Use a fixed seed for reproducibility
print("Circuit diagram (logical gates, uncompiled):")
logical_circuit.draw()
print()

# --- 1b. Compile the logical circuit to the custom native gate set ---
print(">>> 1b. Compiling the logical circuit to your custom native gate set...")
# We now create an experiment instance that uses the custom native gates.
# The compiler will decompose the logical fSim gates into this native set.
native_exp = StandardXEBExperiment(
    qubits=[0, 1],
    native_gates=list(CUSTOM_NATIVE_GATES.keys())
)
compiled_circuit = native_exp.generate_single_circuit(depth=2, seed=1) # Use same seed to compile the same logical circuit
print("Circuit diagram (compiled to your custom native basis):")
compiled_circuit.draw()
print()

# --- 1c. Generate an Interleaved circuit ---
print(">>> 1c. Generating an Interleaved XEB circuit with a parameterized U3 gate...")
# This demonstrates interleaving a custom gate. It will also be compiled to the custom native basis.
interleaved_gate = Gate('u3', (0,), params=[np.pi/2, np.pi/4, -np.pi/4])
interleaved_exp = InterleavedXEBExperiment(
    qubits=[0, 1],
    interleaved_gate=interleaved_gate,
    native_gates=list(CUSTOM_NATIVE_GATES.keys())
)
interleaved_circuit = interleaved_exp.generate_single_circuit(depth=3, seed=2)
print(f"Compiled circuit with '{interleaved_gate.name}' gate interleaved on qubit {interleaved_gate.qubits[0]}:")
interleaved_circuit.draw()
print()


# ================================================================================
# // PART 2: BULK CIRCUIT GENERATION FOR EXPERIMENTS
# ================================================================================
print("="*80)
print("// PART 2: BULK CIRCUIT GENERATION FOR EXPERIMENTS")
print("="*80)
print("\nThis demonstrates using the framework as a 'circuit generator' for large-scale")
print("experiments, all compiled to your custom native gate set.\n")

bulk_depths = [10, 20, 30, 40, 50]
circs_per_depth = 20
# This experiment will use the custom native gates specified.
bulk_exp = StandardXEBExperiment(
    qubits=[0, 1, 2, 3],
    depths=bulk_depths,
    circuits_per_depth=circs_per_depth,
    native_gates=list(CUSTOM_NATIVE_GATES.keys())
)
all_circuits = bulk_exp.circuits()
print(f"SUCCESS: Generated a total of {len(all_circuits)} circuits for depths {bulk_depths}.")
print("These circuit objects are compiled to your native basis and can be exported.\n")


# ================================================================================
# // PART 3: AUTOMATED END-TO-END EXPERIMENT
# ================================================================================
print("="*80)
print("// PART 3: AUTOMATED END-TO-END EXPERIMENT")
print("="*80)
print("\nThis shows the full, automated workflow using your custom native configuration:")
print("defining an experiment, running it, and getting the final benchmark result (EPC).\n")

print("Running automated XEB analysis on qubits [0, 1]...")
# This experiment is also configured to use the custom native gates.
automated_exp = StandardXEBExperiment(
    qubits=[0, 1],
    depths=[0, 4, 6, 8, 10, 12, 14, 16],
    circuits_per_depth=15,
    seed=42,
    native_gates=list(CUSTOM_NATIVE_GATES.keys())
)

print("A plot window will appear. Please close it to continue the script.")
# The run method executes the circuits (already compiled to the custom basis) on the backend.
results = automated_exp.run(engine, shots=8096)

print("\n--- Analysis Complete ---")
epc = results['xeb_analysis']['fit_results']['epc']
print(f"Fitted Error Per Clifford (EPC) from XEB: {epc:.5f}")

p_sq_val = results['spb_analysis']['fit_results']['p_sq']
print(f"Fitted Purity Decay Parameter (p²) from SPB: {p_sq_val:.5f}")

print("\n================================================================================")
print("DEMO COMPLETE: All stages executed successfully using your custom native gates.")
print("================================================================================")