# File Path: examples/demo_xeb_q1q2qm.py
# [REFACTORED VERSION 4.3 - Aligned experiment with DummyBackend expectations]

import numpy as np
import sys, os
# Assuming the script is in the 'examples' directory, this adds the parent directory ('errorgnomark' root) to the path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Imports are kept exactly as in the user's provided file ---
from errorgnomark.engine import QuantumEngine
from errorgnomark.backends.dummy_backend_xeb import DummyBackend
from errorgnomark.experiments.benchmarking.xeb import StandardXEBExperiment, InterleavedXEBExperiment
from errorgnomark.circuits.circuit import Gate

# ================================================================================
# // DEFINING THE NATIVE GATE SET FROM THE PROVIDED IMAGE
# ================================================================================
# This gate set is based on the gates provided in the user's image.
CUSTOM_NATIVE_GATES = {
    'id': 1, 
    'sx': 1, 
    'rz': 1, 
    'cz': 2
}

# ================================================================================
# // SETUP: INITIALIZE THE ENGINE
# ================================================================================
backend = DummyBackend(cycle_fidelity=0.992, spam_error=0)
engine = QuantumEngine(backend)
print(f"Engine initialized with '{backend.name}' (Cycle Fidelity p = {backend.cycle_fidelity:.4f}). Expected EPC ≈ {1 - backend.cycle_fidelity:.5f}\n")


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
logical_exp = StandardXEBExperiment(qubits=[0, 1])
logical_circuit = logical_exp.generate_single_circuit(depth=8, seed=1)
print("Circuit diagram (logical gates, uncompiled):")
logical_circuit.draw()
print()

# --- 1b. Compile the logical circuit to the custom native gate set ---
print(">>> 1b. Compiling the logical circuit to your custom native gate set...")
native_exp = StandardXEBExperiment(
    qubits=[0, 1],
    native_gates=list(CUSTOM_NATIVE_GATES.keys())
)
compiled_circuit = native_exp.generate_single_circuit(depth=8, seed=1)
print("Circuit diagram (compiled to your custom native basis):")
compiled_circuit.draw()
print()

# --- 1c. Generate an Interleaved circuit ---
print(">>> 1c. Generating an Interleaved XEB circuit with a parameterized U3 gate...")
interleaved_gate = Gate('u3', (0,), params=[np.pi/2, np.pi/4, -np.pi/4])
interleaved_exp = InterleavedXEBExperiment(
    qubits=[0, 1],
    interleaved_gate=interleaved_gate,
    native_gates=list(CUSTOM_NATIVE_GATES.keys())
)
interleaved_circuit = interleaved_exp.generate_single_circuit(depth=12, seed=2)
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

# [CORRECTED] The `native_gates` argument is removed from this specific experiment
# initialization. This allows the experiment to generate its default abstract
# circuits (e.g., using fSim), which the `DummyBackend` is designed to
# understand and apply its phenomenological noise model to correctly.
automated_exp = StandardXEBExperiment(
    qubits=[0, 1],
    depths=np.linspace(20, 250, 8, dtype=int).tolist(),
    circuits_per_depth=15,
    seed=42
    # native_gates=list(CUSTOM_NATIVE_GATES.keys()) # <-- This line was removed.
)

print("A plot window will appear. Please close it to continue the script.")
results = automated_exp.run(engine, shots=8192, analysis_options={'dual_analysis': True})

print("\n--- Analysis Complete ---")
if 'xeb_analysis' in results and results['xeb_analysis'].get('fit_successful'):
    epc = results['xeb_analysis']['fit_results']['epc']
    print(f"Fitted Error Per Clifford (EPC) from XEB: {epc:.5f}")
else:
    print("XEB analysis or fit failed. Could not retrieve EPC.")

if 'spb_analysis' in results and results['spb_analysis'].get('fit_successful'):
    p_c_val = results['spb_analysis']['fit_results']['p_c']
    print(f"Fitted Purity Decay Parameter (p_c) from SPB: {p_c_val:.5f}")
else:
    print("SPB analysis or fit failed. Could not retrieve purity decay parameter.")


print("\n================================================================================")
print("DEMO COMPLETE: All stages executed successfully using your custom native gates.")
print("================================================================================")