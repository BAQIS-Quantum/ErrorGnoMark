# File Path: examples/demo_xeb_professional.py
# [DEFINITIVE FINAL VERSION - Rebuilt for Clarity and Feature Parity with RB Demo]
#
# ErrorGnomark: Professional Cross-Entropy Benchmarking (XEB) Demonstration
#
# This script is a self-documenting tutorial demonstrating the advanced features
# of the XEB module, now aligned with the rest of the framework. It shows:
# 1. The clean separation of concerns: Experiments PREPARE, the Engine EXECUTES.
# 2. Control over circuit decomposition via the `native_gates` parameter to switch
#    between Logical and Physical circuit views.
# 3. How to benchmark both standard (CZ) and parameterized (U3) gates using
#    the unified InterleavedXEBExperiment interface.

import sys
import os
import numpy as np

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

# --- Framework Imports (Using the new, unified API) ---
from errorgnomark.engine import QuantumEngine
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.xeb import StandardXEBExperiment, InterleavedXEBExperiment
from errorgnomark.circuits.circuit import Gate

# Define a common native gate set for CNOT-based hardware for demonstration
IBM_Q_NATIVE_GATES = ['cnot', 'sx', 'x', 'rz', 'id']


# =========================================================================
# --- Main Demonstration Script ---
# =========================================================================

if __name__ == "__main__":

    print("=" * 79)
    print("      Professional Cross-Entropy Benchmarking (XEB) Demonstration")
    print("=" * 79)
    print("This demo showcases the XEB module's advanced features, including")
    print("circuit decomposition control and parameterized gate benchmarking.\n")

    # --- 1. Framework Setup ---
    print("[STEP 1] Setting up a backend and ONE universal quantum engine...")
    backend = DummyBackend(
        depolarizing_error_1q=0.003,
        depolarizing_error_2q=0.005,
    )
    engine = QuantumEngine(backend=backend)
    print("QuantumEngine initialized and ready.")
    print("-" * 79 + "\n")

    # --- Shared Experiment Parameters ---
    xeb_depths = [2, 4, 6, 8, 12, 16, 20] # Shorter depths for faster demo
    xeb_circuits_per_depth = 10
    xeb_shots = 4096

    # --- 2. The Core Concept: Logical vs. Physical Circuits (XEB Edition) ---
    print("[STEP 2] The Core Concept: Controlling XEB Circuit Decomposition.")
    print("         Just like RB, the XEB Experiment can generate different 'views'.\n")
    
    target_cz_gate = Gate('cz', [0, 1])
    viz_depth = 2
    
    # --- 2a. The Logical "Blueprint" ---
    print("[2a] The 'Blueprint': A Logical View (Decomposition Disabled)")
    print("     To see the abstract circuit, we explicitly pass `native_gates=None`.")
    logical_exp = StandardXEBExperiment(qubits=[0, 1], native_gates=None)
    logical_circuit = logical_exp.generate_single_circuit(depth=viz_depth, seed=42)
    logical_circuit.draw()
    print("     This view shows the ideal gates used by the XEB sequence (e.g., T, H, CZ).\n")

    # --- 2b. The Default Physical "Execution Plan" ---
    print("[2b] The 'Default Execution Plan': Physical View (Default CZ-Basis)")
    print("     Without `native_gates`, the Experiment uses its smart default (CZ-basis).")
    physical_exp_default = StandardXEBExperiment(qubits=[0, 1])
    physical_circuit_default = physical_exp_default.generate_single_circuit(depth=viz_depth, seed=42)
    physical_circuit_default.draw()
    print("     Here, non-native gates like 'T' are decomposed into the default basis (e.g., Rz).\n")
    
    # --- 2c. The Custom Physical "Execution Plan" ---
    print("[2c] The 'Custom Execution Plan': Targeting a CNOT-based Backend")
    print("     We can target different hardware by providing a custom `native_gates` list.")
    ibm_physical_exp = StandardXEBExperiment(qubits=[0, 1], native_gates=IBM_Q_NATIVE_GATES)
    ibm_physical_circuit = ibm_physical_exp.generate_single_circuit(depth=viz_depth, seed=42)
    ibm_physical_circuit.draw()
    print("     Now, the native 'CZ' gate from the XEB sequence has been compiled to CNOT!\n")
    print("-" * 79 + "\n")

    # --- 3. Two-Qubit Standard XEB ---
    print("[STEP 3] Run 2-Qubit Standard XEB.")
    print("     This runs on PHYSICALLY DECOMPOSED circuits (default CZ-basis) for a realistic EPC.")
    std_exp_2q = StandardXEBExperiment(
        qubits=[0, 1],
        depths=xeb_depths,
        circuits_per_depth=xeb_circuits_per_depth
    )
    results_2q_std = std_exp_2q.run(engine, shots=xeb_shots, plot=True, verbose=False)
    epc_2q = results_2q_std['fit_results']['error_per_cycle']
    print(f"         > Result: Estimated 2Q EPC = {epc_2q:.6f}")
    print("Plotting 2Q Standard XEB results... Please close the plot window to continue.")
    plt.show()
    print("-" * 79 + "\n")

    # --- 4. Two-Qubit Interleaved XEB for CZ ---
    print("[STEP 4] Run Physically-Correct Interleaved XEB for the CZ gate.")
    print("     This measures the fidelity of the CZ gate's PHYSICAL IMPLEMENTATION.")
    int_exp_cz = InterleavedXEBExperiment(
        qubits=[0, 1],
        interleaved_gate=target_cz_gate,
        depths=xeb_depths,
        circuits_per_depth=xeb_circuits_per_depth
    )
    results_cz_int = int_exp_cz.run(engine, shots=xeb_shots, plot=True, verbose=False)
    cz_error = results_cz_int['gate_error_results']['error_per_gate']
    print(f"         > Result: Estimated CZ Gate Error = {cz_error:.6f}")
    print("Plotting Interleaved XEB for CZ... Please close the plot window to continue.")
    plt.show()
    print("-" * 79 + "\n")

    # --- 5. Interleaved XEB for a Parameterized Gate ---
    print("[STEP 5] Run Interleaved XEB for a specific parameterized U3 gate.")
    print("     We target a CNOT-basis to measure the fidelity of its compiled form.")
    target_u3_gate = Gate('u3', [0], params=[np.pi/2, 1.2, -0.5])
    
    irb_u3_exp = InterleavedXEBExperiment(
        qubits=[0],
        interleaved_gate=target_u3_gate,
        depths=xeb_depths,
        circuits_per_depth=xeb_circuits_per_depth,
        native_gates=IBM_Q_NATIVE_GATES,
    )
    results_u3_int = irb_u3_exp.run(engine, shots=xeb_shots, plot=True, verbose=False)
    u3_error = results_u3_int['gate_error_results']['error_per_gate']
    print(f"         > Result: Estimated U3 Gate Error = {u3_error:.6f}")
    print(f"Plotting IXEB results for the U3 gate... Please close the plot window to continue.")
    plt.show()
    print("-" * 79 + "\n")

    # --- 6. Final Message ---
    print("\n" + "=" * 79)
    print("Demonstration Finished Successfully.")
    print("You have seen how the XEB module now fully supports decomposition")
    print("control and benchmarking of arbitrary parameterized gates.")
    print("=" * 79)