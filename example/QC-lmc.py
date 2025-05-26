"""
User Guide: ErrorGnoMark Quantum Chip Diagnostic & Benchmarking (Local/Cloud QC System)

This guide demonstrates how to use the ErrorGnoMark software suite for comprehensive quantum chip diagnostics and benchmarking.
Users can flexibly customize chip structure, qubit selection, and the set of metrics to evaluate, supporting both local and cloud QC platforms.

Core Features:
- Supports single-, two-, and multi-qubit benchmarking, error diagnosis, and application-level algorithm evaluation.
- Customizable for chip name, number of qubits, starting qubit, specific benchmarks to run, and more.
- Compatible with local or remote (cloud) quantum computing control systems.
"""

# Step 1. Import Required Packages and Modules
from errorgnomark.errorgnomarker import Errorgnomarker
from errorgnomark.token_manager import define_token, get_token

# Step 2: Define Your Token
define_token("yout token here") # Replace with your actual token

# Step 2: Initialize the Errorgnomarker
# Use simulation mode or real hardware mode
egm = Errorgnomarker(
    chip_name="Baihua",
    result_get='noisysimulation',  # 'hardware' For real hardware mode
                                   # 'noisysimulation' For simulation
    qubit_to_be_used=4,           # Enter the number of qubits to use
    start_qubit=50,                 # Choose the starting qubit index
    file_path=r"./Baihua_calibration_2025-05-26 07_46_48.csv", # 
    # This file contains the latest published calibration information for the Baihua quantum chip as of May 26, 2025.
    weights={
        'T1': 0.5,                 # Adjust the weight ratio for each coefficient in the calculation of qubit scores.
        'T2': 0.5,                 # This weight is used to automatically select other qubits starting from start_qubit.
        'Fidelity': 0,
        'Frequency': 0
    },                             # Default is None. Connectivity score accounts for 80% + T1, T2, Fidelity, and Frequency scores account for 20%.
    run_all_Qubits=True,          # Select all qubits. If run_all_Execute=True, qubit_to_be_used and start_qubit will be ignored.
    rbq1_selected=True,            # Execute Single Qubit RB for Q1
    xebq1_selected=True,           # Execute Single Qubit XEB for Q1
    csbq1_selected=True,           # Execute Single Qubit CSB for Q1
    rbq2_selected=True,            # Execute Two Qubit RB for Q2
    xebq2_selected=True,           # Execute Two Qubit XEB for Q2
    csbq2_selected=True,           # Execute Two Qubit CSB for Q2
    csbq2_cnot_selected=True,      # Execute Two Qubit CNOT CSB
    ghzqm_selected=True,           # Execute m-Qubit GHZ Fidelity
    qvqm_selected=True,            # Execute m-Qubit StanQV Fidelity
    mrbqm_selected=True,           # Execute m-Qubit MRB Fidelity.
                                   # If run_all_Execute=False,
                                   # For MRB to run, the selected qubit indices cannot exceed 31.
                                   # If run_all_Execute=True, the fixed selection is [2,3,4,5,6,7,8,15,16,17,29,30]
    clopsqm_selected=True,         # Execute m-Qubit Speed CLOPS
    vqeqm_selected=True            # Execute m-Qubit VQE
)  # 'noisysimulation' For simulation mode
# egm = Errorgnomarker(chip_name="Baihua", result_get='hardware')  # For real hardware mode

# Step 3: Run Diagnostics and Benchmarking
results, filepath = egm.egm_run()

# Step 4: Visualize Results
egm.draw_visual_table(filepath=filepath)   # Draw the visual table for selected metrics
egm.plot_visual_figure(filepath=filepath)  # Plot the visual figures for selected metrics

# Results are saved in the data_egm folder, along with tables and figures if enabled.
