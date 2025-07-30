# examples/run_single_xeb_experiment.py
import os
import sys

# --- Crucial path fix ---
# This ensures we can import 'errorgnomark' from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 1. Import required components from our layered architecture ---
from errorgnomark.experiments.benchmarking.xeb import XEBExperiment
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.engine.runner import Runner
from errorgnomark.analysis.benchmarking.xeb_analysis import analyze_xeb_fidelity

def main():
    """
    A high-level example demonstrating how to use our framework to run a 
    single XEB experiment.
    """
    # --- 2. Define experiment parameters ---
    target_qubit = 0
    circuit_depth = 20
    noise_level = 0.01 # Simulated hardware noise level

    print("="*60)
    print("Running Single XEB Experiment via Layered Architecture")
    print("="*60)
    print(f"Parameters: Qubits=[{target_qubit}], Depth={circuit_depth}, Noise Level={noise_level}\n")

    # --- 3. Assemble components (following the architecture design) ---
    # a. Define an experiment ("what to do")
    experiment = XEBExperiment(
        qubits=[target_qubit],
        depths=[circuit_depth],
        num_circuits=1,
        gate_set="clifford"
    )

    # b. Initialize a backend ("where to do it")
    backend = DummyBackend(depolarizing_error=noise_level)

    # c. Create a runner to connect the experiment and backend ("how to do it")
    runner = Runner(backend=backend)
    
    print("\n--- Starting Execution ---")
    # --- 4. Execute the workflow ---
    # The Runner handles circuit generation and execution on the backend
    raw_results = runner.run(experiment)
    print("--- Execution Finished ---\n")

    # --- 5. Analyze the results ---
    # We only ran one circuit, so we take the first element from the results list
    single_run_result = raw_results[0]
    
    # Call the dedicated analysis function
    fidelity = analyze_xeb_fidelity(single_run_result, num_qubits=1)

    # --- 6. Report the final results ---
    print("--- Analysis Report ---")
    print(f"Ideal Probabilities:    {single_run_result['ideal_probs']}")
    print(f"Noisy Probabilities:    {single_run_result['noisy_probs']}")
    print("-" * 25)
    print(f"Calculated XEB Fidelity: {fidelity:.6f}")
    print("-" * 25)

    # Theoretical expectation for validation
    expected_fidelity = (1 - noise_level)**circuit_depth
    print(f"Theoretical Expectation: {expected_fidelity:.6f}")
    print("="*60)

if __name__ == "__main__":
    main()