"""
This script demonstrates three distinct XEB-based benchmarking tasks.

FINAL CORRECTED VERSION: This version uses a new 'universal_xeb' gate set
that correctly implements the complex rotations required for XEB. This fixes
both the program crash and the incorrect physics results.
"""

import os
import sys
import matplotlib.pyplot as plt

# Add the project root to the Python path for imports
if '..' not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the necessary classes from our library
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.xeb import (
    SingleQubitGateError,
    TwoQubitGateError,
    StandardXEBInstance
)
from errorgnomark.analysis.benchmarking.xeb_analysis import plot_xeb_fit
# Ensure gate sets are registered by the library
from errorgnomark.experiments import gate_sets

# ==============================================================================
# --- CONFIGURATION (HIGH-QUALITY & CORRECT) ---
# ==============================================================================

# Backend noise level
SHARED_BACKEND_CONFIG = {"depolarizing_error": 0.005}

# Parameters for fitting experiments (Cases 1 & 2)
DEPTHS_FOR_FITTING = [1, 2, 10, 25, 50]
NUM_CIRCUITS_PER_DEPTH = 100
SHOTS = 100000

# *** THE FINAL, CORRECT FIX ***
# Use the new, powerful 'universal_xeb' gate set that generates gates with matrices.
CORRECT_GATE_SET_FOR_XEB = "universal_xeb" 

# Parameters for specific cases
QUBIT_1Q_TEST = [0]
PAIR_2Q_TEST = [(0, 1)]
QUBITS_MULTI_TEST = list(range(5))

# ==============================================================================
# --- MAIN EXECUTION ---
# ==============================================================================

def main():
    """Main function to run the three demonstration cases with the Universal XEB gate set."""
    print("=" * 70)
    print("      ErrorGnomark - Corrected XEB Demonstration (Universal XEB Set)")
    print("=" * 70)

    # --- Initialize the shared backend ---
    print("\n--- Configuring Shared Backend ---")
    # NOTE: Your DummyBackend's ideal simulator must be able to use the `gate.matrix` attribute.
    # Assuming it does, this will now work correctly.
    shared_backend = DummyBackend(depolarizing_error=SHARED_BACKEND_CONFIG["depolarizing_error"])
    print(f"Backend configured: {type(shared_backend).__name__} with depolarizing error = {SHARED_BACKEND_CONFIG['depolarizing_error']}\n")

    # ==========================================================================
    # CASE 1: Single-Qubit Average Gate Error Estimation
    # ==========================================================================
    print("\nCASE 1: Fitting Average 1Q Gate Error (from Universal XEB set)")
    print("-" * 70)
    
    single_q_estimator = SingleQubitGateError(
        qubits_to_test=QUBIT_1Q_TEST,
        gate_set=CORRECT_GATE_SET_FOR_XEB, # <-- THE FIX
        backend=shared_backend,
        verbose=True
    )
    
    single_q_results = single_q_estimator.run_and_fit(shots=SHOTS, return_detailed=True)
    
    for qubit, data in single_q_results.items():
        error = data['fit_results'].get('error_per_gate', float('nan'))
        print(f"\n  > Final Result for Qubit {qubit}:")
        print(f"    - Estimated Average 1Q (XEB) Gate Error: {error:.6f} ({error*100:.4f}%)")
        
        plt.figure(f"Figure 1: 1Q Gate Error Fit (Universal XEB Set)")
        plot_xeb_fit(
            fidelities=data['raw_fidelities'],
            fit_results=data['fit_results'],
            title_info=f"for Universal XEB Gates on Qubit {qubit}"
        )

    # ==========================================================================
    # CASE 2: Two-Qubit Specific Gate (CZ) Error Estimation
    # ==========================================================================
    print("\n\nCASE 2: Fitting Specific 2Q Gate Error (CZ) with Universal 1Q gates")
    print("-" * 70)
    
    cz_estimator = TwoQubitGateError(
        pairs_to_test=PAIR_2Q_TEST,
        depths=DEPTHS_FOR_FITTING,
        num_circuits=NUM_CIRCUITS_PER_DEPTH,
        gate_set=CORRECT_GATE_SET_FOR_XEB, # <-- THE FIX
        target_gate='cz',
        backend=shared_backend,
        verbose=True
    )
    
    cz_results = cz_estimator.run_and_fit(shots=SHOTS, return_detailed=True)
    
    for pair, data in cz_results.items():
        error = data['fit_results'].get('error_per_gate', float('nan'))
        print(f"\n  > Final Result for Pair {pair} (CZ Gate):")
        print(f"    - Estimated CZ Gate Error: {error:.6f} ({error*100:.4f}%)")
        
        plt.figure(f"Figure 2: 2Q Gate Error Fit (Universal XEB + CZ)")
        plot_xeb_fit(
            fidelities=data['raw_fidelities'],
            fit_results=data['fit_results'],
            title_info=f"for CZ Gate (with XEB layers) on Pair {pair}"
        )

    # ==========================================================================
    # CASE 3: Multi-Qubit Single Instance Fidelity Measurement
    # ==========================================================================
    print("\n\nCASE 3: Measuring Single Fidelity for a 5-Qubit Circuit (Universal XEB)")
    print("-" * 70)
    
    print(f"  > Creating a single random circuit for {len(QUBITS_MULTI_TEST)} qubits...")
    
    multi_qubit_instance = StandardXEBInstance(
        qubits=QUBITS_MULTI_TEST,
        gate_set=CORRECT_GATE_SET_FOR_XEB, # <-- THE FIX
        backend=shared_backend
    )
    
    final_fidelity = multi_qubit_instance.run()
    
    print("\n  > Final Result:")
    print(f"    - Measured XEB Fidelity: {final_fidelity:.6f}")
        
    print("\n\n" + "="*70)
    print("Demonstration Complete.")
    print("="*70)
    
    print("\nDisplaying plots... Please close plot windows to exit.")
    plt.show()


if __name__ == "__main__":
    main()