# examples/csb-q1q2.py

import os
import sys
import numpy as np

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from errorgnomark.circuits.circuit import Gate
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.benchmarking.csb import ChannelSpectrumBenchmarkingExperiment

def main():
    """
    An example script demonstrating the use of the Channel Spectrum Benchmarking (CSB)
    experiment for both single-qubit and two-qubit gates.
    
    This script showcases a logically consistent workflow where the tested gate,
    the experimental design, and the analysis model are all aligned.
    """
    print("==============================================================")
    print("=  Running CSB Benchmark using the High-Level Experiment API  =")
    print("==============================================================")

    shots = 8192
    depolarizing_error = 0.0015  # Incoherent error

    # --- Define distinct, intuitive error models for single- and two-qubit gates ---
    
    # Single-qubit gate: A simple phase error (simulating an Rz rotation error)
    gate_angle_error_1q = 0.02 
    
    # Two-qubit gate: A single coherent error parameter that our analysis can detect.
    theta_error_2q = -0.008

    # ===================================================================
    # Example 1: Single-Qubit Gate (X Gate) - Using a single angle error
    # ===================================================================
    print("\n--- Starting Single-Qubit Gate (X Gate) Benchmark ---")
    
    x_gate = Gate(name='X', qubits=(0,))
    
    backend_1q = DummyBackend(
        depolarizing_error=depolarizing_error,
        gate_angle_error=gate_angle_error_1q,
    )
    
    csb_experiment_1q = ChannelSpectrumBenchmarkingExperiment(
        gate_to_benchmark=x_gate,
        max_length=40,
        reps=1
    )
    
    csb_experiment_1q.run_and_analyze(backend=backend_1q, shots=shots, verbose=True)

    # ===================================================================
    # Example 2: Two-Qubit Gate (CZ Gate) - Using a single Theta error
    # ===================================================================
    # MODIFICATION 1: Changed title and gate from CNOT to CZ.
    # This is the most critical change. The CSB experiment as designed in `csb.py`
    # assumes the gate's eigenstates are the computational basis states (|00>, |01>, etc.).
    # CZ gate fits this assumption perfectly, while CNOT does not. This ensures
    # the experiment is physically measuring what the analysis model expects.
    print("\n\n--- Starting Two-Qubit Gate (CZ Gate) Benchmark ---")
    
    cz_gate = Gate(name='CZ', qubits=(0, 1))
    
    # MODIFICATION 2: Simplified the injected error to match the analysis capability.
    # Our `analyze_csb_data_2q` function is designed to extract one primary angle
    # error ('theta_error'). By only injecting that same error here, we create a
    # clean, verifiable test: the final reported error should be very close to -0.008.
    backend_2q = DummyBackend(
        depolarizing_error=depolarizing_error,
        systematic_theta_error=theta_error_2q,
        # systematic_phi_error is removed to create a clear test case.
    )
    
    csb_experiment_2q = ChannelSpectrumBenchmarkingExperiment(
        gate_to_benchmark=cz_gate,
        max_length=40,
        reps=1
    )
    
    csb_experiment_2q.run_and_analyze(backend=backend_2q, shots=shots, verbose=True)
    
    print("\n\nAll benchmarks completed.")

if __name__ == "__main__":
    main()