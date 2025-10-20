# File: demo_rb_q1q2.py
# Description: A comprehensive demonstration of the Randomized Benchmarking
#              workflow in the errorgnomark framework. This script relies on
#              the corrected library functions.
# [VERSION 3.2 - Simplified for User Clarity, Professional English]

import numpy as np
import logging
import matplotlib.pyplot as plt

# --- Framework Imports ---
# This script assumes the library `errorgnomark` has been corrected.
try:
    from errorgnomark.experiments.benchmarking.rb import StandardRBExperiment, InterleavedRBExperiment
    from errorgnomark.engine import QuantumEngine
    from errorgnomark.backends.dummy_backend import DummyBackend
    from errorgnomark.circuits.circuit import Gate
    from errorgnomark.analysis.rb import fit_rb_data, plot_rb_single
except ImportError as e:
    print(f"ImportError: {e}")
    print("Please ensure you run this script from the project's root directory,")
    print("or that the 'errorgnomark' package is installed in your Python environment.")
    exit()

# Configure logging for clear, professional output
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Define a default physical gate set for clarity in the demo
DEFAULT_PHYSICAL_GATES = ['sx', 'rz', 'h', 's', 'cz']

# =========================================================================
# Main Demo Workflow
# =========================================================================

def main():
    """Main function to execute the RB demonstration workflow."""
    DEMO_SEED = 42
    print(f"Using a fixed seed ({DEMO_SEED}) for reproducibility in this demo.")

    # =========================================================================
    # 1. Generate and Draw a Single LOGICAL RB Circuit
    # =========================================================================
    print("\n" + "="*70)
    print(" Part 1: Generate and Draw a Single LOGICAL 2-Qubit RB Circuit")
    print("="*70)

    # Initialize a Standard RB experiment. 'qubits' is a required argument.
    # We explicitly set 'seed' to ensure the demo is reproducible.
    logical_rb_exp = StandardRBExperiment(
        qubits=[0, 1],
        seed=DEMO_SEED
        # NOTE: The following parameters are using their default values from the library:
        # - native_gates=None (circuits remain at the logical Clifford level)
        # - depths=[1, 10, 20, 40, 60, 80, 100, 125]
        # - circuits_per_depth=25
    )
    
    print("Generating a single logical RB circuit with Clifford depth m=10...")
    # 'depth' is a required argument for this specific function call.
    single_logical_circuit = logical_rb_exp.generate_single_circuit(depth=10)
    print("Drawing the logical circuit (Clifford gates are shown as abstract blocks):")
    print(single_logical_circuit.draw())
    input("\nPress Enter to continue to Part 2...")

    # =========================================================================
    # 2. Decompose Circuit to a Physical Gate Set
    # =========================================================================
    print("\n" + "="*70)
    print(" Part 2: Decompose Circuit to a Physical Gate Set")
    print("="*70)

    # For this experiment, we provide 'native_gates' to demonstrate the
    # automatic decomposition of Clifford gates.
    physical_rb_exp = StandardRBExperiment(
        qubits=[0, 1],
        native_gates=DEFAULT_PHYSICAL_GATES,
        seed=DEMO_SEED
        # NOTE: 'depths' and 'circuits_per_depth' are using their default values.
    )

    print(f"Generating the same circuit, but now decomposed into the gate set: {DEFAULT_PHYSICAL_GATES}")
    single_physical_circuit = physical_rb_exp.generate_single_circuit(depth=10)
    print("Drawing the decomposed (physical) circuit:")
    print(single_physical_circuit.draw())
    input("\nPress Enter to continue to Part 3...")

    # =========================================================================
    # 3. Set up and Visualize an Interleaved RB (IRB) Circuit
    # =========================================================================
    print("\n" + "="*70)
    print(" Part 3: Set up and Visualize an Interleaved RB (IRB) Circuit")
    print("="*70)
    cz_gate_to_interleave = Gate('cz', qubits=[0, 1])
    
    # Initialize an Interleaved RB experiment. 'qubits' and 'interleaved_gate' are required.
    irb_exp_setup = InterleavedRBExperiment(
        qubits=[0, 1],
        interleaved_gate=cz_gate_to_interleave,
        seed=DEMO_SEED
        # NOTE: 'native_gates', 'depths', and 'circuits_per_depth' are using defaults.
    )

    print(f"Generating a single IRB circuit to benchmark the '{cz_gate_to_interleave.name.upper()}' gate...")
    single_irb_circuit = irb_exp_setup.generate_single_circuit(depth=5)
    print("Drawing the logical IRB circuit:")
    print(single_irb_circuit.draw())
    print("Notice the 'interleaved_gate_name' in the metadata below:")
    print(single_irb_circuit.metadata)
    input("\nPress Enter to continue to Part 4...")

    # =========================================================================
    # 4. Analyze and Plot Pre-existing RB Data
    # =========================================================================
    print("\n" + "="*70)
    print(" Part 4: Analyze Pre-existing RB Data")
    print("="*70)
    print("SCENARIO: Analyzing a pre-existing dataset of survival probabilities.\n")
    mock_depths = [1, 10, 25, 50, 75, 100, 125]
    p_true, A_true, B_true = 0.99, 0.75, 0.25
    np.random.seed(DEMO_SEED)
    mock_survival_data = {d: [max(0, min(1, A_true * (p_true ** d) + B_true + np.random.normal(scale=0.02))) for _ in range(20)] for d in mock_depths}
    
    print("Fitting data using the 'fit_rb_data' analysis tool...")
    fit_results = fit_rb_data(mock_survival_data, num_qubits=2)
    
    if fit_results['fit_successful']:
        print(f"Fit successful! Calculated Error Per Clifford (EPC) = {fit_results['epc']:.4e}")
        print("Generating plot using 'plot_rb_single' from the library...")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        plot_rb_single(
            results=fit_results, 
            num_qubits=2, 
            title="Analysis of Pre-existing RB Data (2 Qubits)",
            ax=ax
        )
        
        plt.tight_layout()
        plt.show()
    else:
        print("Fitting failed for the mock data.")
    input("\nPress Enter to continue to Part 5...")

    # =========================================================================
    # 5. Run and Analyze a Full End-to-End Interleaved RB Experiment
    # =========================================================================
    print("\n" + "="*70)
    print(" Part 5: End-to-End IRB Test with the Corrected DummyBackend")
    print("="*70)
    
    # Define fidelities for the backend to simulate a realistic noisy device.
    CLIFFORD_FIDELITY = 0.98  # Fidelity of a random Clifford, p_C
    CZ_FIDELITY = 0.99        # Fidelity of the interleaved CZ gate, p_G
    SPAM_ERROR = 0.005

    print(f"Initializing DummyBackend with p_C = {CLIFFORD_FIDELITY} and p_G(CZ) = {CZ_FIDELITY}")
    my_backend = DummyBackend(
        clifford_fidelity=CLIFFORD_FIDELITY,
        gate_fidelities={'cz': CZ_FIDELITY}, # Crucial for simulating the interleaved gate's error
        spam_error_rate=SPAM_ERROR
    )
    my_engine = QuantumEngine(backend=my_backend)
    NUM_SHOTS = 1024

    # The InterleavedRBExperiment class runs both the standard and interleaved
    # experiments and performs the analysis in one go.
    
    print("\n--- Running Full Interleaved RB Experiment Workflow ---")
    irb_full_exp = InterleavedRBExperiment(
        qubits=[0, 1], 
        depths=mock_depths, # Using custom depths for this specific demo
        interleaved_gate=Gate('cz', qubits=[0, 1]),
        native_gates=DEFAULT_PHYSICAL_GATES, 
        seed=DEMO_SEED
        # NOTE: 'circuits_per_depth=25' is being used as it's the library default.
    )
    
    # This single .run() call will:
    # 1. Run the standard RB reference experiment.
    # 2. Run the interleaved RB experiment.
    # 3. Analyze both results and calculate EPG for the 'CZ' gate.
    # 4. Plot the comparison graph.
    irb_results = irb_full_exp.run(
        engine=my_engine, 
        shots=NUM_SHOTS
        # NOTE: 'plot=True' is the default behavior, so it is omitted for simplicity.
    )
    
    if not irb_results:
        print("\nIRB experiment failed to produce results.")
    
    print("\n" + "="*70)
    print(" Demo Finished Successfully.")
    print("="*70)

if __name__ == "__main__":
    main()