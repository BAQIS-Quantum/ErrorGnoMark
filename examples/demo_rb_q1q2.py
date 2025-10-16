# File Path: examples/demo_rb_professional.py
# [DEFINITIVE FINAL VERSION - Enhanced for Clarity and Educational Value]
#
# ErrorGnomark: Professional Randomized Benchmarking Demonstration
#
# This script serves as a complete, self-documenting tutorial. It demonstrates:
# 1. The framework's clean architecture: Experiments PREPARE, the Engine EXECUTES.
# 2. The critical distinction between "Logical" and "Physical" circuits.
# 3. How to control circuit decomposition via the `native_gates` parameter:
#    - Explicitly disabling it for a logical view (`native_gates=None`).
#    - Relying on the smart default for a common physical view (CZ-basis).
#    - Customizing it for a specific hardware target (CNOT-basis).
# 4. The importance of using physically-correct, decomposed circuits for realistic
#    fidelity estimation in RB.
# 5. Benchmarking both standard (CNOT) and parameterized (U3) gates.

import sys
import os
import numpy as np

# =========================================================================
# --- PLOTTING FIX: Force an Interactive Matplotlib Backend ---
# This is often necessary to make plots appear when running scripts from the command line.
import matplotlib
matplotlib.use('TkAgg')
# =========================================================================

import matplotlib.pyplot as plt

# --- Python Path Setup ---
try:
    # This will work if errorgnomark is installed as a package
    import errorgnomark
except ImportError:
    # This is the fallback for running directly from the repository
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# --- Framework Imports (Using the final, correct API) ---
from errorgnomark.engine import QuantumEngine
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.rb import StandardRBExperiment, InterleavedRBExperiment
from errorgnomark.circuits.circuit import Gate

# Define a common native gate set for CNOT-based hardware (e.g., IBM Quantum)
IBM_Q_NATIVE_GATES = ['cnot', 'sx', 'x', 'rz', 'id']


# =========================================================================
# --- Main Demonstration Script ---
# =========================================================================

if __name__ == "__main__":

    print("=" * 79)
    print("      Professional Randomized Benchmarking (RB) Demonstration")
    print("=" * 79)
    print("This demo showcases the framework's clean architecture and the critical")
    print("concept of circuit decomposition for physical realism.\n")

    # --- 1. Framework Setup: A Single Backend and a Single Engine ---
    print("[STEP 1] Setting up a backend and ONE universal quantum engine...")
    backend = DummyBackend(
        depolarizing_error_1q=0.001,
        depolarizing_error_2q=0.01,
        t_gate_error=0.002,
    )
    engine = QuantumEngine(backend=backend)
    print("QuantumEngine initialized and ready.")
    print("-" * 79 + "\n")

    # --- Shared Experiment Parameters ---
    rb_depths = [1, 10, 20, 30, 50, 75, 100, 125]
    rb_num_sequences = 20
    rb_shots = 2048

    # --- 2. The Core Concept: Logical vs. Physical Circuits ---
    print("[STEP 2] The Core Concept: Controlling Circuit Decomposition.")
    print("         An 'Experiment' can generate circuits in different 'views'.\n")
    
    target_cnot_gate = Gate('cnot', [0, 1])
    viz_depths = [1]
    viz_sequences = 1
    
    # --- 2a. The Logical "Blueprint" ---
    print("[2a] The 'Blueprint': A Logical View (Decomposition Disabled)")
    print("     To see the pure, abstract circuit, we explicitly pass `native_gates=None`.")
    print("     This disables the decomposition engine.")
    logical_exp = StandardRBExperiment(
        qubits=[0, 1], depths=viz_depths, num_sequences=viz_sequences,
        interleaved_gate=target_cnot_gate, native_gates=None
    )
    logical_circuit = logical_exp.circuits()[0]
    logical_circuit.draw()
    print("     This view is ideal for algorithm design and theoretical analysis.\n")

    # --- 2b. The Default Physical "Execution Plan" ---
    print("[2b] The 'Default Execution Plan': Physical View (Default CZ-Basis)")
    print("     If we do not specify `native_gates`, the Experiment uses its smart default:")
    print("     a common CZ-based gate set. CNOT is not in this set.")
    physical_exp_default = StandardRBExperiment(
        qubits=[0, 1], depths=viz_depths, num_sequences=viz_sequences,
        interleaved_gate=target_cnot_gate
        # No `native_gates` argument passed, so it uses the default
    )
    physical_circuit_default = physical_exp_default.circuits()[0]
    physical_circuit_default.draw()
    print("     Notice how the abstract CNOTs are now automatically compiled into H-CZ-H sequences.\n")
    
    # --- 2c. The Custom Physical "Execution Plan" ---
    print("[2c] The 'Custom Execution Plan': Targeting an IBM-like Backend")
    print("     We can target a different hardware by providing a custom `native_gates` list.")
    print("     This list includes 'cnot', so CNOT gates will be preserved.")
    ibm_physical_exp = StandardRBExperiment(
        qubits=[0, 1], depths=viz_depths, num_sequences=viz_sequences,
        interleaved_gate=target_cnot_gate, native_gates=IBM_Q_NATIVE_GATES
    )
    ibm_physical_circuit = ibm_physical_exp.circuits()[0]
    ibm_physical_circuit.draw()
    print("     The circuit is now compiled to a CNOT-based instruction set. Other gates (like Y)")
    print("     have been decomposed into `sx` and `rz` gates.\n")

    # --- 2d. Automatic Decomposition of Any Gate ---
    print("[2d] The Power of Decomposition: Handling Arbitrary Gates")
    print("     The engine can decompose any gate, including parameterized ones like U3.")
    target_u3_gate = Gate('u3', [0], params=[np.pi/2, 1.2, -0.5])
    u3_physical_exp = StandardRBExperiment(
        qubits=[0], depths=viz_depths, num_sequences=viz_sequences,
        interleaved_gate=target_u3_gate, 
        native_gates=IBM_Q_NATIVE_GATES
    )
    u3_physical_circuit = u3_physical_exp.circuits()[0]
    u3_physical_circuit.draw()
    print("     The abstract U3 gate is seamlessly compiled into the specified physical basis.")
    print("-" * 79 + "\n")

    # --- 3. Two-Qubit Standard RB ---
    print("[STEP 3] Run 2-Qubit Standard RB.")
    print("     By default, this runs on PHYSICALLY DECOMPOSED circuits (CZ-basis),")
    print("     giving a realistic measure of the average gate fidelity.")
    std_exp_2q = StandardRBExperiment(
        qubits=[0, 1],
        depths=rb_depths,
        num_sequences=rb_num_sequences
    )
    std_exp_2q.run(engine, shots=rb_shots, plot=True, verbose=False) # verbose=False for cleaner output
    print("Plotting 2Q Standard RB results... Please close the plot window to continue.")
    plt.show()
    print("-" * 79 + "\n")

    # --- 4. Two-Qubit Interleaved RB for CNOT ---
    print("[STEP 4] Run Physically-Correct Interleaved RB for the CNOT gate.")
    print("     This measures the fidelity of the CNOT gate's PHYSICAL IMPLEMENTATION (H-CZ-H).")
    correct_irb_exp = InterleavedRBExperiment(
        qubits=[0, 1],
        interleaved_gate=target_cnot_gate,
        depths=rb_depths,
        num_sequences=rb_num_sequences
    )
    correct_irb_exp.run(engine, shots=rb_shots, plot=True, verbose=False)
    print("Plotting Correct Interleaved RB... Note the physically meaningful fidelity.")
    print("Please close the plot window to continue.")
    plt.show()
    print("-" * 79 + "\n")

    # --- 5. Interleaved RB for a Parameterized Gate ---
    print("[STEP 5] Run Interleaved RB for a specific parameterized U3 gate.")
    print("     We target an IBM-like basis to measure the fidelity of its compiled form.")
    irb_u3_exp = InterleavedRBExperiment(
        qubits=[0],
        interleaved_gate=target_u3_gate,
        depths=rb_depths,
        num_sequences=rb_num_sequences,
        native_gates=IBM_Q_NATIVE_GATES,
    )
    irb_u3_exp.run(engine, shots=rb_shots, plot=True, verbose=False)
    print(f"Plotting IRB results for the U3 gate... Please close the plot window to continue.")
    plt.show()
    print("-" * 79 + "\n")

    # --- 6. Final Message ---
    print("\n" + "=" * 79)
    print("Demonstration Finished Successfully.")
    print("You have seen how to control circuit compilation and run realistic,")
    print("physically-aware benchmarking experiments.")
    print("=" * 79)