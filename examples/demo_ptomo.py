# File: examples/demo_ptomo.py
# [FINAL v13] - QPT Demo + Excel Report Generation (independent framework)

import os, sys, numpy as np

# --- Add project path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# --- Framework Imports ---
from egm.engine.executor import QuantumEngine
from egm.core.circuits.circuit import QuantumCircuit, Gate
from egm.experiments.characterization.tomography.process_tomography import ProcessTomographyExperiment
from egm.core.backends.flexible_statevector_backend import FlexibleStatevectorBackend

# --- Reporting and Visualization Imports ---
from egm.analysis.reporting import ExcelReport, generate_report
from egm.analysis.process_tomography import compare_pauli_transfer_matrices

# =======================================================
def demo_qpt_cnot():
    """
    Demonstrates fully independent Quantum Process Tomography (QPT)
    on a 2-qubit CNOT gate, including Excel reporting.
    """
    num_qubits = 2
    shots = 8096
    noise = 0

    header = f"{num_qubits}-Qubit QPT for CNOT (Independent Framework)"
    print("=" * len(header))
    print(header)
    print("=" * len(header))

    # 1️ Build backend and engine
    backend = FlexibleStatevectorBackend(
        depolarizing_error_1q=noise,
        depolarizing_error_2q=noise * 2
    )
    engine = QuantumEngine(backend=backend)

    # 2️ Define CNOT process
    cnot_circ = QuantumCircuit(qubits=[0, 1])
    cnot_circ.add_gate(Gate('cnot', (0, 1)))
    print("\n[INFO] Target process circuit:")
    cnot_circ.draw()
    print("-" * 80)

    # 3️ Build + run experiment
    qpt_exp = ProcessTomographyExperiment(
        process_circuit=cnot_circ,
        qubits=[0, 1]
    )
    print("[STEP 1] Running 2-qubit QPT...")
    raw_counts = qpt_exp.run(engine, shots=shots, verbose=True)
    print("[INFO] Raw experimental tomography data collected.")
    print("-" * 80)

    # 4️ Analyze data and compute Fidelity
    print("[STEP 2] Reconstructing process (linear inversion)...")
    result = qpt_exp.analyze(ideal_process_circuit=cnot_circ)
    choi_rec = result.data["reconstructed_choi"]
    fidelity = result.data["process_fidelity"]
    print(f"[Result] Process Fidelity (vs CNOT): {fidelity:.4f}")

    # 5️ Visualization (Pauli Transfer Matrix)
    print("[STEP 3] Visualizing PTMs (Ideal vs Estimate)...")
    ideal_choi = qpt_exp._get_ideal_choi(cnot_circ)
    compare_pauli_transfer_matrices(ideal_choi, choi_rec, num_qubits)

    # 6️ Console report
    print("[STEP 4] Generating console summary...")
    generate_report([result])

    # 7️ Excel Report
    print("[STEP 5] Exporting Excel report...")
    report = ExcelReport(output_dir="qpt_reports")
    report.create_summary_sheet(
        [result],
        experiment_params={
            "Experiment Type": "Quantum Process Tomography",
            "Target Process": "CNOT",
            "Qubits": "[0,1]",
            "Shots": shots,
            "Backend": backend.name,
            "Noise": noise
        }
    )

    # --- Add heatmap plots to Excel ---
    report.add_chi_matrix_plot(choi_rec, sheet_name="Reconstructed Chi Matrix")
    report.add_chi_matrix_plot(ideal_choi, sheet_name="Ideal Chi Matrix")

    # --- Add raw counts ---
    flat_counts = {}
    for prep_label, meas_dict in raw_counts.items():
        for meas_label, counts in meas_dict.items():
            basis_key = f"{prep_label}_{meas_label}"
            flat_counts[basis_key] = counts
    report.add_counts_sheet(flat_counts)

    save_path = report.save("qpt_demo_report_cnot")
    print(f"[SUCCESS] Excel report saved to {save_path}")

    print("\n" + "=" * len(header))
    print("Demonstration completed successfully.")
    print("=" * len(header))


if __name__ == "__main__":
    demo_qpt_cnot()