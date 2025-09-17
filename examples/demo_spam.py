# examples/demo_spam_characterization.py

import sys
import os
import numpy as np

# --- Add the project root to the Python path ---
# This part of your code is slightly different from previous versions, so we'll keep it.
# It seems you might have reorganized files, e.g., runner is now in engine.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# -------------------------------------------------

# The imports are based on the file you provided.
from errorgnomark.experiments.characterization.spam import SPAMCharacterization
from errorgnomark.backends.dummy_backend import DummyBackend
# Assuming 'engine' is the correct new location for Runner
from errorgnomark.engine.runner import Runner 
# Assuming this is the correct new location for spam_analysis
from errorgnomark.analysis.characterization.spam_analysis import analyze_spam

def main():
    """
    Main function to run the SPAM characterization demo.
    """
    print("============================================================")
    print("  ERRORGNOMARK: SPAM CHARACTERIZATION DEMO")
    print("============================================================")
    print()

    # --- [1] Define Experiment Parameters and Initialize Backend ---
    print("------------------------------------------------------------")
    print("[1] Initializing Backend and Runner...")
    print("------------------------------------------------------------")
    
    target_qubit = 0
    shots = 8192
    spam_error_rate = 0.01

    # Initialize the DummyBackend with a defined SPAM error.
    spam_backend = DummyBackend(spam_error=spam_error_rate)
    
    # The Runner class requires the backend object during initialization.
    runner = Runner(backend=spam_backend)
    
    # The print statement in the backend's __init__ is now the source of truth.
    # We can simplify the print statements here.
    print(f"  - Runner: Initialized and linked with backend.")
    print()

    # --- [2] Run the SPAM Characterization Experiment ---
    print("------------------------------------------------------------")
    print("[2] Running SPAM Characterization Experiment...")
    print("------------------------------------------------------------")
    
    # Instantiate the experiment class.
    spam_exp = SPAMCharacterization(qubits=[target_qubit], backend=spam_backend)
    
    # The runner executes the experiment's circuits.
    # The variable 'results' will contain the raw output from the backend via the runner.
    # Its format will be [(probabilities, counts), (probabilities, counts)]
    results = runner.run(
        experiment=spam_exp,
        shots=shots
    )
    
    print("Runner: Experiment execution finished.")
    print()

    # --- [3] Analyze the Results and Display the SPAM Matrix ---
    print("------------------------------------------------------------")
    print("[3] Analyzing and Displaying SPAM Results...")
    print("------------------------------------------------------------")
    
    try:
        # --- DATA TRANSFORMATION FIX ---
        # 'results' is in the format [(probs, counts), ...].
        # 'analyze_spam' expects [(counts, metadata), ...].
        # We must perform a transformation here.

        # 1. Get the circuits that were run to access their metadata.
        circuits_that_ran = spam_exp.generate_circuits()

        # 2. Create a new list in the correct format.
        results_for_analysis = []
        for raw_result, circuit in zip(results, circuits_that_ran):
            # raw_result is a tuple: (probabilities, counts)
            counts = raw_result[1]  # The counts dictionary is the second element.
            metadata = circuit.metadata  # Get metadata from the corresponding circuit.
            results_for_analysis.append((counts, metadata))
        
        # 3. Pass the correctly formatted data to the analysis function.
        spam_analysis = analyze_spam(results_for_analysis, qubits=[target_qubit])

        if spam_analysis.get('error'):
            print(f"  > Analysis failed: {spam_analysis['error']}")
            return

        # Display the confusion matrix
        print("  > SPAM Analysis Complete. Confusion Matrix:")
        print("    ------------------------------------------")
        print(f"    - P(meas=0|prep=0): {spam_analysis['p0_given_0']:.4f}  (Fidelity of |0>)")
        print(f"    - P(meas=1|prep=0): {spam_analysis['p1_given_0']:.4f}  (Error)")
        print("    ------------------------------------------")
        print(f"    - P(meas=1|prep=1): {spam_analysis['p1_given_1']:.4f}  (Fidelity of |1>)")
        print(f"    - P(meas=0|prep=1): {spam_analysis['p0_given_1']:.4f}  (Error)")
        print("    ------------------------------------------")
        print()
        print(f"  > Expected values with {spam_error_rate*100}% SPAM error:")
        print(f"    - Fidelity terms (P(0|0), P(1|1)) should be approx. {1 - spam_error_rate:.4f}")
        print(f"    - Error terms (P(1|0), P(0|1)) should be approx. {spam_error_rate:.4f}")
        print()

    except Exception as e:
        # A general catch-all for any unexpected errors during analysis.
        import traceback
        print(f"  > An unexpected error occurred during analysis: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()