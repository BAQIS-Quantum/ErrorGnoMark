# run_entanglement_tests.py
import os
import sys
from pprint import pprint
from typing import List

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# /Users/ousiachai/Desktop/errgnomarkv2/examples/entanglement_verifications.py

# --- Core Imports from your library ---
from errorgnomark.analysis.benchmarking.entanglement_verification import (
    BellStateVerification,
    GHZStateVerification,
    WStateVerification
)
# Make sure you have a DummyBackend to import. Let's assume its location is:
from errorgnomark.backends.dummy_backend import DummyBackend

# --- Main Execution Block ---
if __name__ == "__main__":
    # =========================================================================
    # CRITICAL FIX: Create an INSTANCE of the DummyBackend class here.
    # We create it once and reuse it for all experiments.
    # =========================================================================
    print("Initializing a DummyBackend instance for all experiments...")
    dummy_backend = DummyBackend()  # Use a lowercase variable name for the instance

    print("-" * 50)

    # --- Example 1: Verifying a 2-Qubit Bell State ---
    print("\n>>> Running Bell State Verification <<<")
    bell_qubits = [0, 1]
    print(f"Target Qubits: {bell_qubits}")
    
    bell_experiment = BellStateVerification(qubits=bell_qubits, shots=4096)
    
    # =========================================================================
    # CRITICAL FIX: Pass the INSTANCE (dummy_backend), not the CLASS (DummyBackend).
    # =========================================================================
    bell_results = bell_experiment.run(backend=dummy_backend)

    print("\n--- Bell State Results ---")
    print(f"Calculated Fidelity: {bell_results['fidelity']:.4f}")
    print(f"Ideal Outcomes: {bell_results['ideal_outcomes']}")
    print(f"Raw Measurement Counts: {bell_results['raw_counts']}")
    bell_experiment.print_last_circuit()
    print("-" * 50)

    # --- Example 2: Verifying a 3-Qubit GHZ State ---
    print("\n>>> Running GHZ State Verification <<<")
    ghz_qubits = [2, 4, 6]
    print(f"Target Qubits: {ghz_qubits}")
    
    ghz_experiment = GHZStateVerification(qubits=ghz_qubits, shots=4096)
    
    # Pass the same backend instance here
    ghz_results = ghz_experiment.run(backend=dummy_backend)

    print("\n--- GHZ State Results ---")
    print(f"Calculated Fidelity: {ghz_results['fidelity']:.4f}")
    print(f"Ideal Outcomes: {ghz_results['ideal_outcomes']}")
    print(f"Raw Measurement Counts: {ghz_results['raw_counts']}")
    ghz_experiment.print_last_circuit()
    print("-" * 50)

    # --- Example 3: Verifying a 4-Qubit W State ---
    print("\n>>> Running W State Verification <<<")
    w_qubits = [0, 1, 2, 3]
    print(f"Target Qubits: {w_qubits}")
    
    w_experiment = WStateVerification(qubits=w_qubits, shots=8192)
    
    # Pass the same backend instance here
    w_results = w_experiment.run(backend=dummy_backend)

    print("\n--- W State Results ---")
    print(f"Calculated Fidelity: {w_results['fidelity']:.4f}")
    print(f"Ideal Outcomes: {w_results['ideal_outcomes']}")
    print(f"Raw Measurement Counts: {w_results['raw_counts']}")
    w_experiment.print_last_circuit()
    print("-" * 50)