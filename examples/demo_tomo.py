# File Path: examples/demo_tomo.py
# [ADAPTED VERSION - Now uses the FlexibleStatevectorBackend]

import sys
import os
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# --- Python Path Setup ---
try:
    import errorgnomark
except ImportError:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path: sys.path.insert(0, project_root)

# --- Framework Imports ---
from errorgnomark.engine import QuantumEngine
# =========================================================================
# [MODIFIED CODE - CHANGE 1]
from errorgnomark.backends.flexible_statevector_backend import FlexibleStatevectorBackend
# =========================================================================
from errorgnomark.circuits.circuit import QuantumCircuit, Gate
from errorgnomark.experiments.characterization.tomography.state_tomography import StateTomographyExperiment
from errorgnomark.analysis.reporting import generate_report, plot_density_matrix, ExcelReport

if __name__ == "__main__":
    print("=" * 79)
    print("   2-Qubit Quantum State Tomography (QST) Demonstration")
    print("   >>> Using FlexibleStatevectorBackend with Noise <<<")
    print("=" * 79)

    # --- 1. Framework Setup ---
    print("[INFO] Setting up a simulated backend and quantum engine...")

    backend = FlexibleStatevectorBackend(
        depolarizing_error_1q=0.005,
        depolarizing_error_2q=0.02
    )
    # =========================================================================
    engine = QuantumEngine(backend=backend)
    print("-" * 79 + "\n")

    # --- 2. Define the State to Characterize (Bell State) ---
    print("[STEP 1] Defining the state preparation circuit for a Bell state |Φ+>.")
    qubits = [0, 1]
    bell_state_circuit = QuantumCircuit(qubits)
    bell_state_circuit.add_gate(Gate('h', (0,)))
    bell_state_circuit.add_gate(Gate('cx', (0, 1))) 
    print(str(bell_state_circuit))
    print("-" * 79 + "\n")

    # --- 3. Initialize and Run the Tomography Experiment ---
    print("[STEP 2] Initializing and running the tomography experiment...")
    shots = 8192
    tomo_exp = StateTomographyExperiment(qubits, bell_state_circuit)
    

    raw_results = tomo_exp.run(engine, shots=shots, verbose=True)
    print(f"\nExample raw result for 'XX' basis: {raw_results.get('XX', {})}")
    print("-" * 79 + "\n")

    # --- 4. Analyze the Results ---
    print("[STEP 3] Analyzing the collected data...")
    ideal_statevector = engine.get_ideal_statevector(bell_state_circuit)
    
    linear_results = tomo_exp.analyze(ideal_state=ideal_statevector, method='linear')
    dfe_results = tomo_exp.analyze(ideal_state=ideal_statevector, method='dfe')
    analysis_results = linear_results + dfe_results
    
    # --- 5. Report the Findings ---
    print("\n[STEP 4] Generating reports...")
    
    # 5a. Console Report
    generate_report(analysis_results)
    
    # 5b. Plot the reconstructed density matrix (from the Linear Inversion method)
    linear_result = linear_results[0]
    reconstructed_rho = linear_result.data['reconstructed_rho']
    plot_density_matrix(reconstructed_rho, title="Reconstructed Density Matrix (Linear Inversion)")
    print("Displaying density matrix plot... Please close the plot window to continue.")
    plt.show()

    # 5c. Create a comprehensive Excel Report
    if ExcelReport:
        report = ExcelReport(output_dir="reports")
        
        report.create_summary_sheet(
            analysis_results,
            experiment_params={"qubits": qubits, "shots_per_basis": shots, "target_state": "Bell |Φ+>"}
        )
        
        report.add_counts_sheet(tomo_exp.results['raw_counts'])
        report.add_probabilities_sheet(tomo_exp.results['raw_counts'])
        
        report.add_density_matrix_plot(reconstructed_rho, sheet_name="Reconstructed Rho")
        
        report_path = report.save("Tomography_Report_Bell_State_Flexible_Backend")
    
    print("\n" + "=" * 79)
    print("Tomography Demonstration finished successfully.")
    print("=" * 79)