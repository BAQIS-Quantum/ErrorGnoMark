# File Path: examples/demo_prb.py
# [DEFINITIVE FINAL VERSION v2.0 - Simplified calls using default parameters]

import numpy as np
import matplotlib.pyplot as plt

# --- Import necessary components from the library ---
# Assume these paths are correct relative to the project root
from egm.engine.executor import QuantumEngine
from egm.core.backends.dummy_backend import DummyBackend
from egm.experiments.benchmarking.prb import (
    StandardPRBExperiment,
    InterleavedPRBExperiment
)

def main():
    """
    Demonstrates the Professional Purity Randomized Benchmarking (PRB) workflow,
    leveraging smart default parameters for maximum simplicity.
    """
    print("=" * 79)
    print("   Professional Purity Randomized Benchmarking (PRB) Demonstration")
    print("=" * 79)
    print("This demo relies on default parameters for maximal simplicity.\n")

    # --- Setup ---
    print("[INFO] Setting up a simulated backend and quantum engine...")
    
    # Initialize the backend using the correct v2.0 parameters.
    backend = DummyBackend(
        clifford_fidelity=0.98,
        gate_fidelities={'H': 0.98, 'CNOT': 0.95},
        spam_error_rate=0.0001
    )
    
    # Initialize the quantum engine with our backend.
    engine = QuantumEngine(backend=backend)

    print("-" * 79 + "\n")

    # ==========================================================================
    # STEP 1: Generate and inspect a sample circuit pair
    # ==========================================================================
    print("[STEP 1] Generate a single, reproducible 1-Qubit PRB circuit pair.")
    # We can instantiate the experiment with minimal parameters.
    demo_exp = StandardPRBExperiment(qubits=[0])
    circuit_a, circuit_b = demo_exp._generate_circuit_pair(depth=3, seed=123)
    
    print("         Sample Circuit A (with Pauli Twirl, depth=3):")
    print(f"{circuit_a}\n")
    print("         Sample Circuit B (without Pauli Twirl, depth=3):")
    print(f"{circuit_b}")
    print("-" * 79 + "\n")

    # ==========================================================================
    # STEP 2: Run a full 1-Qubit Standard PRB Experiment
    # ==========================================================================
    print("[STEP 2] Run 1-Qubit Standard PRB using default parameters.")
    
    # We can now omit `depths` and `circuits_per_depth` to use the smart defaults.
    # The class will automatically select appropriate depths based on the number of qubits.
    # Default depths for 1 qubit: [1, 10, 25, 40, 60, 80, 100]
    # Default circuits_per_depth: 30
    # (我们可以省略 `depths` 和 `circuits_per_depth` 来使用智能默认值。)
    # (该类会基于量子比特数自动选择合适的深度。)
    # (1-qubit 默认深度: [1, 10, 25, 40, 60, 80, 100])
    # (默认 circuits_per_depth: 30)
    std_prb_1q = StandardPRBExperiment(qubits=[0])
    
    std_results_1q = std_prb_1q.run(engine, shots=4096, verbose=True)
    std_analysis_1q = std_prb_1q.analyze_results(std_results_1q, plot=True)
    print("-" * 79 + "\n")

    # ==========================================================================
    # STEP 3: Run a full 2-Qubit Standard PRB Experiment
    # ==========================================================================
    print("[STEP 3] Run 2-Qubit Standard PRB using default parameters.")

    # Again, we rely on the default parameters for simplicity.
    # Default depths for 2 qubits: [1, 5, 10, 20, 40, 60, 80]
    # Default circuits_per_depth: 30
    # (再次，我们依赖默认参数以简化调用。)
    # (2-qubit 默认深度: [1, 5, 10, 20, 40, 60, 80])
    # (默认 circuits_per_depth: 30)
    std_prb_2q = StandardPRBExperiment(qubits=[0, 1])
    
    std_results_2q = std_prb_2q.run(engine, shots=4096, verbose=True)
    std_analysis_2q = std_prb_2q.analyze_results(std_results_2q, plot=True)
    print("-" * 79 + "\n")

    # ==========================================================================
    # STEP 4: Run a 2-Qubit Interleaved PRB Experiment to benchmark CNOT
    # ==========================================================================
    print("[STEP 4] Run 2-Qubit Interleaved PRB to benchmark the CNOT gate.")
    
    # For Interleaved PRB, we only need to specify the target gate.
    # The `depths` and `circuits_per_depth` will be automatically synchronized
    # with the `std_results_2q` data when we call the `.run()` method.
    # This ensures the baseline and interleaved data have matching x-axes for plotting.
    # (对于交叉PRB，我们只需指定目标门。)
    # (当我们调用 `.run()` 方法时，`depths` 和 `circuits_per_depth` 将会)
    # (与传入的 `std_results_2q` 数据自动同步。)
    # (这确保了基准和交叉实验数据在绘图时具有匹配的x轴。)
    int_prb_cnot = InterleavedPRBExperiment(
        qubits=[0, 1],
        target_gate_name='CNOT'
    )
    
    # The `.run()` method now handles the logic of using the provided baseline results.
    # It will automatically run the interleaved experiment with the SAME depths
    # as the `std_results_2q` baseline experiment.
    interleaved_results = int_prb_cnot.run(
        engine, 
        shots=4096, 
        standard_results=std_results_2q, # Pass the baseline results here
        verbose=True
    )
    final_analysis = int_prb_cnot.analyze_results(interleaved_results, plot=True)
    
    print("\n--- Final Analysis Summary ---")
    cnot_error = final_analysis.get("interleaved_gate_error_analysis", {}).get("gate_error")
    if cnot_error is not None:
        print(f"Estimated CNOT Gate Error: {cnot_error:.4f} (or Fidelity: {1-cnot_error:.4f})")
    else:
        print("Could not determine CNOT gate error.")

    print("\nDemonstration finished successfully.")
    print("=" * 79)
    
    print("\n[INFO] Displaying generated plots. Please close plot windows to exit.")
    plt.show() # This command displays all generated figures.


if __name__ == "__main__":
    main()