# File Path: examples/demo_astate_tomo.py (run_state_tomography.py)
# FINAL CORRECTED VERSION - Fixes the AttributeError by using the public API of DummyBackend.

import os
import sys
from datetime import datetime
import numpy as np
from typing import Dict, Tuple

# Ensure the project root is in the Python path to find the 'errorgnomark' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.backends.base_backend import BaseBackend
from errorgnomark.backends.dummy_backend import DummyBackend
from errorgnomark.experiments.characterization.tomography.state_tomography.arbitrary_state_tomography import ArbitraryStateTomographyExperiment
from errorgnomark.analysis.reporting import generate_report, ExcelReport, plot_density_matrix

def main():
    """
    Runs the state tomography experiment using the default DummyBackend.
    """
    print("="*80)
    print("=== RUNNING DEMO WITH DEFAULT DummyBackend ===")
    print("="*80)

    # --- [Step 1] Setup Results Directory ---
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = os.path.join("results", f"tomography_dummy_backend_{timestamp}")
    os.makedirs(results_dir, exist_ok=True)
    print(f"--- All results will be saved in: {results_dir} ---")

    # --- [Step 2] Initialize Backend with Noise ---
    print("\n[Step 2] Initializing backend (Depolarizing: 0.005, SPAM: 0.01)...")
    depolarizing_error = 0.005
    spam_error = 0.01
    # Note: The DeprecationWarning you see is normal if DummyBackend prefers new params.
    # The main demo uses legacy params to show backward compatibility.
    backend = DummyBackend(depolarizing_error=depolarizing_error, spam_error=spam_error)

    # --- [Step 3] Define Target State ---
    print("\n[Step 3] Defining target state: Bell state on qubits [0, 1].")
    qubits_to_test = [0, 1]
    bell_circuit = QuantumCircuit(qubits=qubits_to_test)
    bell_circuit.add_gate(Gate('h', (0,)))
    bell_circuit.add_gate(Gate('cnot', (0, 1)))

    # --- [Step 4] Run Tomography Experiment ---
    print("\n[Step 4] Running experiment to collect Pauli expectation values (8192 shots per basis)...")
    shots_per_basis = 8192
    experiment = ArbitraryStateTomographyExperiment(qubits=qubits_to_test, state_prep_circuit=bell_circuit)
    experiment.run(backend, shots=shots_per_basis)
    raw_data = experiment.experiment_data

    # --- [Step 5] Analyze the results using different methods ---
    print("\n[Step 5] Analyzing the results...")
    analysis_tool = experiment.analysis_tool
    
    ideal_bell_vector = (1/np.sqrt(2)) * np.array([1, 0, 0, 1])
    ideal_bell_rho = np.outer(ideal_bell_vector, ideal_bell_vector.conj())

    result_tomography = analysis_tool.analyze(experiment_data=raw_data, ideal_density_matrix=ideal_bell_rho)
    result_dfe = analysis_tool.analyze(experiment_data=raw_data, target_state_vector=ideal_bell_vector)
    analysis_results = [result_tomography, result_dfe]

    # --- [Step 6] Generate All Reports and Outputs ---
    print("\n[Step 6] Generating all reports and output files...")

    bases_filepath = os.path.join(results_dir, "measurement_bases.txt")
    with open(bases_filepath, 'w') as f:
        for basis in experiment.measurement_bases:
            f.write(f"{basis}\n")
    print(f"Measurement bases saved to: {bases_filepath}")

    plot_save_path = os.path.join(results_dir, "reconstructed_density_matrix.png")
    plot_density_matrix(
        rho=result_tomography.reconstructed_rho,
        title="Reconstructed Density Matrix (from Noisy Simulation)",
        save_path=plot_save_path
    )

    report = ExcelReport(results_dir)
    report.create_summary_sheet(
        analysis_results=analysis_results,
        experiment_params={
            "Target State": "Bell State |Φ+⟩",
            "Qubits": qubits_to_test,
            "Shots per Basis": shots_per_basis,
            "Depolarizing Error": depolarizing_error,
            "SPAM Error": spam_error,
            "Backend": "DummyBackend"
        }
    ).add_raw_data_sheet(
        experiment_data=raw_data
    ).add_probabilities_sheet(
        experiment_data=raw_data
    ).add_density_matrix_plot(
        rho=result_tomography.reconstructed_rho,
        sheet_name="Reconstructed Density Matrix"
    )
    report_path = report.save("tomography_report")
    print(f"Excel report saved to: {report_path}")

    # --- Final Console Report ---
    print("\n[Step 7] Displaying final console summary...")
    generate_report(analysis_results)


# ==============================================================================
# === NEW EXAMPLE: Integrating and Using a Custom User-Defined Backend ===
# ==============================================================================

class CustomSimulatorBackend(BaseBackend):
    """
    An example custom backend that simulates a new simulator with a specific, 
    simple noise model. This class demonstrates how to implement the BaseBackend interface.
    
    Noise Model: A simple bit-flip probability is applied to the measurement outcomes.
    """
    def __init__(self, bit_flip_error: float = 0.02):
        if not (0 <= bit_flip_error <= 1):
            raise ValueError("Bit-flip error must be between 0 and 1.")
        self.bit_flip_error = bit_flip_error
        print(f"[CustomBackend] Initialized with bit-flip error = {self.bit_flip_error}")

    def run(self, circuit: QuantumCircuit, shots: int) -> Tuple[Dict[str, float], Dict[str, int]]:
        # --- [FIX] ---
        # The private method '_simulate' no longer exists on DummyBackend.
        # We must use the public API 'run()' to get the ideal probabilities.
        # We also use the new, non-deprecated parameters for initialization.
        temp_ideal_backend = DummyBackend(
            depolarizing_error_1q=0, 
            depolarizing_error_2q=0, 
            spam_error=0
        )
        
        # Call the public 'run' method. We only need the ideal probabilities,
        # so we can ignore the second return value (counts).
        # We pass shots=1 because the method requires it, but the value doesn't matter for ideal probs.
        ideal_probabilities, _ = temp_ideal_backend.run(circuit, shots=1)
        # --- [END FIX] ---

        num_qubits = len(circuit.qubits)
        noisy_probabilities = {format(i, f'0{num_qubits}b'): 0.0 for i in range(2**num_qubits)}

        for ideal_outcome, ideal_prob in ideal_probabilities.items():
            if ideal_prob < 1e-9:
                continue
            
            for i in range(2**num_qubits):
                noisy_outcome = format(i, f'0{num_qubits}b')
                num_flips = sum(c1 != c2 for c1, c2 in zip(ideal_outcome, noisy_outcome))
                prob_of_this_flip = (self.bit_flip_error ** num_flips) * \
                                    ((1 - self.bit_flip_error) ** (num_qubits - num_flips))
                noisy_probabilities[noisy_outcome] += ideal_prob * prob_of_this_flip
        
        # We need a way to sample from these probabilities. We can reuse the
        # internal _sample_from_probabilities method from our temp_ideal_backend.
        # Note: Accessing private methods is generally not recommended, but here it's
        # a pragmatic choice to avoid re-writing the sampling logic.
        noisy_counts = temp_ideal_backend._sample_from_probabilities(noisy_probabilities, shots)
        return (ideal_probabilities, noisy_counts)


def run_with_custom_backend():
    """
    A complete demonstration of running the full analysis workflow with a custom backend.
    """
    print("\n\n" + "="*80)
    print("=== RUNNING DEMO WITH CUSTOM USER-DEFINED BACKEND ===")
    print("="*80)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = os.path.join("results", f"tomography_custom_backend_{timestamp}")
    os.makedirs(results_dir, exist_ok=True)
    print(f"--- All results will be saved in: {results_dir} ---")

    print("\n[Step 2] Initializing our CustomSimulatorBackend...")
    custom_backend = CustomSimulatorBackend(bit_flip_error=0.015)

    print("\n[Step 3] Defining target state: Bell state on qubits [0, 1].")
    qubits_to_test = [0, 1]
    bell_circuit = QuantumCircuit(qubits=qubits_to_test)
    bell_circuit.add_gate(Gate('h', (0,)))
    bell_circuit.add_gate(Gate('cnot', (0, 1)))

    print("\n[Step 4] Running experiment on the custom backend (8192 shots per basis)...")
    shots_per_basis = 8192
    experiment = ArbitraryStateTomographyExperiment(qubits=qubits_to_test, state_prep_circuit=bell_circuit)
    
    experiment.run(custom_backend, shots=shots_per_basis)
    raw_data = experiment.experiment_data

    print("\n[Step 5] Analyzing the results from the custom backend...")
    analysis_tool = experiment.analysis_tool
    
    ideal_bell_vector = (1/np.sqrt(2)) * np.array([1, 0, 0, 1])
    ideal_bell_rho = np.outer(ideal_bell_vector, ideal_bell_vector.conj())

    result_tomography = analysis_tool.analyze(experiment_data=raw_data, ideal_density_matrix=ideal_bell_rho)
    result_dfe = analysis_tool.analyze(experiment_data=raw_data, target_state_vector=ideal_bell_vector)
    analysis_results = [result_tomography, result_dfe]

    print("\n[Step 6] Generating all reports and output files for the custom run...")

    plot_save_path = os.path.join(results_dir, "reconstructed_density_matrix_custom.png")
    plot_density_matrix(
        rho=result_tomography.reconstructed_rho,
        title="Reconstructed Density Matrix (from Custom Backend)",
        save_path=plot_save_path
    )

    report = ExcelReport(results_dir)
    report.create_summary_sheet(
        analysis_results=analysis_results,
        experiment_params={
            "Target State": "Bell State |Φ+⟩",
            "Qubits": qubits_to_test,
            "Shots per Basis": shots_per_basis,
            "Custom Noise": f"Bit-Flip Error = {custom_backend.bit_flip_error}",
            "Backend": "CustomSimulatorBackend"
        }
    ).add_raw_data_sheet(
        experiment_data=raw_data
    ).add_probabilities_sheet(
        experiment_data=raw_data
    ).add_density_matrix_plot(
        rho=result_tomography.reconstructed_rho,
        sheet_name="Reconstructed Density Matrix"
    )
    report_path = report.save("tomography_report_custom")
    print(f"Excel report for custom run saved to: {report_path}")

    print("\n[Step 7] Displaying final console summary for the custom run...")
    generate_report(analysis_results)


if __name__ == "__main__":
    # Run the original main function with the default backend
    main()
    
    # Then, run our new demonstration using the custom backend
    run_with_custom_backend()