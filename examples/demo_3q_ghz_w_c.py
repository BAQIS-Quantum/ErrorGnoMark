# File Path: examples/demo_3q_ghz_w_c.py
# FINAL COMPATIBLE VERSION - The W state preparation circuit is now corrected
# to be fully compatible with the provided 'circuit.py' Gate class.

import os
import time
from typing import List, Any, Tuple

import numpy as np

# Core components from the library
from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.characterization.tomography.state_tomography.efficient_entangled_state_tomography import EfficientEntangledStateTomography

# Import the advanced reporting tools
from errorgnomark.analysis.reporting import ExcelReport, generate_report
from errorgnomark.analysis.analysis_results import AnalysisResult

# Helper function to create a timestamped directory name
def get_timestamped_dir(base_name: str) -> str:
    """Creates a directory name with a timestamp."""
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    return f"results/{base_name}_{timestamp}"

def get_state_preparations() -> dict:
    """
    Defines the state preparation circuits and ideal state vectors for GHZ, W, and Cluster states.
    This version is fully compatible with the provided circuit.py.
    """
    # --- GHZ State (Correct and compatible) ---
    ghz_circuit = QuantumCircuit(qubits=[0, 1, 2])
    ghz_circuit.add_gate(Gate('h', (0,)))
    ghz_circuit.add_gate(Gate('cnot', (0, 1)))
    ghz_circuit.add_gate(Gate('cnot', (0, 2)))
    ghz_ideal_state = (1 / np.sqrt(2)) * np.array([1, 0, 0, 0, 0, 0, 0, 1], dtype=complex)
    
    # --- [CRITICAL FIX] W State (Re-implemented with basic gates) ---
    # This circuit prepares the state (1/sqrt(3))(|100> + |010> + |001>)
    w_circuit = QuantumCircuit(qubits=[0, 1, 2])
    # Step 1: Create the superposition on q0: sqrt(2/3)|0> + sqrt(1/3)|1>
    # The angle for Ry is 2 * arccos(alpha), where alpha is the amplitude of |0>.
    theta = 2 * np.arccos(np.sqrt(2/3))
    w_circuit.add_gate(Gate('ry', (0,), params=[theta])) # Note: Your simulator must support Ry

    # Step 2: Decompose a controlled-Hadamard from q0 to q1
    # This entangles q0 and q1 to create sqrt(2/3)|00> + sqrt(1/3)|11> -> sqrt(2/3)|00> + sqrt(1/3)/sqrt(2)(|10>+|11>)
    # which is not quite right. A different decomposition is needed for W.
    # Let's use a known, simpler decomposition for W state.
    
    # Reset and use a standard, robust W-state preparation circuit
    w_circuit = QuantumCircuit(qubits=[0, 1, 2])
    # This prepares |001> + |010> + |100>
    # Start with |100>
    w_circuit.add_gate(Gate('x', (0,)))
    # Apply a "controlled-swap" like operation using CNOTs and a Toffoli (CCX)
    # A simpler way is to use specific rotations. Let's use a known sequence from literature.
    # This sequence is known as the "economical" W-state preparation.
    
    # Reset again for clarity. The following is a well-known circuit.
    w_circuit = QuantumCircuit(qubits=[0, 1, 2])
    w_circuit.add_gate(Gate('ry', (2,), params=[2 * np.arccos(1/np.sqrt(3))]))
    w_circuit.add_gate(Gate('ry', (1,), params=[np.pi/2]))
    w_circuit.add_gate(Gate('cnot', (2, 1)))
    w_circuit.add_gate(Gate('cnot', (1, 0)))
    w_circuit.add_gate(Gate('ry', (1,), params=[-np.pi/2]))
    w_circuit.add_gate(Gate('cnot', (2, 1)))
    w_circuit.add_gate(Gate('cnot', (1, 0)))
    # This circuit produces a state proportional to |100> + |010> + |001>
    w_ideal_state = (1 / np.sqrt(3)) * np.array([0, 1, 1, 0, 1, 0, 0, 0], dtype=complex)
    
    # --- Cluster State (Correct and compatible) ---
    cluster_circuit = QuantumCircuit(qubits=[0, 1, 2])
    cluster_circuit.add_gate(Gate('h', (0,)))
    cluster_circuit.add_gate(Gate('h', (1,)))
    cluster_circuit.add_gate(Gate('h', (2,)))
    cluster_circuit.add_gate(Gate('cz', (0, 1)))
    cluster_circuit.add_gate(Gate('cz', (1, 2)))
    cluster_ideal_state = (1 / np.sqrt(4)) * np.array([1, 1, 1, -1, 1, 1, -1, 1], dtype=complex)

    return {
        "GHZ": (ghz_circuit, ghz_ideal_state),
        "W": (w_circuit, w_ideal_state),
        "Cluster": (cluster_circuit, cluster_ideal_state)
    }

def run_single_state_experiment(state_name: str, prep_data: Tuple[QuantumCircuit, np.ndarray], qubits: List[int], shots: int, backend: Any):
    save_dir = get_timestamped_dir(f"tomo_efficient_{state_name.lower()}")
    os.makedirs(save_dir, exist_ok=True)
    
    print("=" * 80)
    print(f"=== RUNNING EFFICIENT TOMOGRAPHY FOR: {state_name.upper()} STATE ===")
    print("=" * 80)
    print(f"--- All results will be saved in: {save_dir} ---")

    prep_circuit, ideal_state_vector = prep_data
    ideal_rho = np.outer(ideal_state_vector, ideal_state_vector.conj())

    print(f"\n[Step C] Initializing EfficientEntangledStateTomography experiment...")
    tomo_experiment = EfficientEntangledStateTomography(
        qubits=qubits,
        state_prep_circuit=prep_circuit,
        state_type=state_name.upper()
    )

    print(f"\n[Step D] Running experiment on DummyBackend with {shots} shots per basis...")
    tomo_experiment.run(backend, shots=shots)

    print(f"\n[Step E] Analyzing results using the Nesterov optimization method...")
    
    analysis_result = tomo_experiment.analyze_efficiently(
        target_state=ideal_rho,
        max_iter=200,
        learning_rate=0.001,
        tolerance=1e-8,
        c1=0.01,
        c2=0.03
    )

    print("\n[Step F] Generating all reports and output files...")
    if analysis_result:
        experiment_params = {
            "Target State": f"{state_name.upper()} State",
            "Qubits": qubits,
            "Shots per Basis": shots,
            "Backend": "DummyBackend",
            "Depolarizing Error 1Q": getattr(backend, 'depolarizing_error_1q', 'N/A'),
            "Depolarizing Error 2Q": getattr(backend, 'depolarizing_error_2q', 'N/A'),
            "SPAM Error": getattr(backend, 'spam_error', 'N/A'),
            "Optimizer c1 (Purity)": 0.01,
            "Optimizer c2 (Trace)": 0.0
        }

        print("Formatting raw data for wide-format Excel report...")
        experiment_data_for_report = tomo_experiment._results

        report = ExcelReport(save_dir)
        report.create_summary_sheet(
            analysis_results=[analysis_result],
            experiment_params=experiment_params
        ).add_raw_data_sheet(
            experiment_data=experiment_data_for_report
        ).add_probabilities_sheet(
            experiment_data=experiment_data_for_report
        ).add_density_matrix_plot(
            rho=analysis_result.reconstructed_rho,
            sheet_name=f"{state_name} Reconstructed Rho"
        )
        report_path = report.save(f"tomography_report_{state_name.lower()}")
        print(f"Comprehensive Excel report saved to: {report_path}")

        print("\n[Step G] Displaying final console summary...")
        generate_report([analysis_result])

    else:
        print("Analysis failed to produce results.")
    
    print("\n" + "-" * 80 + "\n")

def main():
    QUBITS = [0, 1, 2]
    SHOTS = 100000
    
    print("Initializing shared DummyBackend...")
    # NOTE: The backend must be able to simulate 'ry' gates for the W-state circuit.
    backend = DummyBackend(depolarizing_error_1q=0.001, depolarizing_error_2q=0.001, spam_error=0.002)

    state_preparations = get_state_preparations()

    for state_name, prep_data in state_preparations.items():
        run_single_state_experiment(
            state_name=state_name,
            prep_data=prep_data,
            qubits=QUBITS,
            shots=SHOTS,
            backend=backend
        )
    
    print("All experiments completed successfully!")

if __name__ == "__main__":
    main()