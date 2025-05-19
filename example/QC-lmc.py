"""
A User Guide for Local QC Measurement & Control System

This script demonstrates how to use the ErrorGnoMark software for quantum chip diagnostics and benchmarking.

If you are using a local quantum computing (QC) measurement and control system, you can access the complete chip information online, including its topology and connectivity.

Notes:
- This example automatically defines a 5x5 chip structure.
- The system selects 9 qubits: [0, 1, 2, 3, 4, 5, 6, 7, 8].
- The chip, qubit index list, and qubit connectivity can be customized by the user.
- To run on an actual chip, users need to register and provide a valid token.
"""

# Import Required Modules
from errorgnomark.errorgnomarker import Errorgnomarker
from errorgnomark.token_manager import define_token, get_token

# Step 1: Define Your Token
# Replace with your actual token
define_token("F8WL`4Y3NBdVhdRzK4Wy84O8[:q9t67K5P4T4i4{ip7/1YO4R{N6JEOvZUN{B{N5dEO4FkPjBIfmKDMjZUN7VkN7BkNhFkNuRENuVkNxJkJ7JDeimnJtBkPjxX[3WHcjxjJvOnM2SX[vRYbjClN3JUO{JENzF{NjpkJzW3d2Kzf")

# Step 2: Initialize the Errorgnomarker
# Use simulation mode or real hardware mode
egm = Errorgnomarker(chip_name="Baihua", result_get='noisysimulation', qubit_to_be_used=12,
                     start_qubit=8,
                     file_path=r"./Baihua_calibration_2025-04-21 12_26_19.csv",
                     weights={'T1': 0.5,
                              'T2': 0.5,
                              'Fidelity': 0,
                              'Frequency': 0},  # 默认 None。连通性0.8 + T1和T2得分 0.2
                     run_all_Execute=False,  # Execute All Task for All Qubits
                     rbq1_selected=True,  # Execute Single Qubit RB for Q1
                     xebq1_selected=True,  # Execute Single Qubit XEB for Q1
                     csbq1_selected=True,  # Execute Single Qubit CSB for Q1
                     rbq2_selected=True,  # Execute Two Qubit RB for Q2
                     xebq2_selected=True,  # Execute Two Qubit XEB for Q2
                     csbq2_selected=True,  # Execute Two Qubit CSB for Q2
                     csbq2_cnot_selected=True,  # Execute Two Qubit CNOT CSB
                     ghzqm_selected=True,  # Execute m-Qubit GHZ Fidelity
                     qvqm_selected=True,  # Execute m-Qubit StanQV Fidelity
                     mrbqm_selected=True,  # Execute m-Qubit MRB Fidelity。
                                           # 为了mrb能运行，所选的qubit序号不能超过31。
                                           # 若使用Run all模式，则固定选择[2,3,4,5,6,7,8,15,16,17,29,30]
                     clopsqm_selected=True,  # Execute m-Qubit Speed CLOPS
                     vqeqm_selected=True  # Execute m-Qubit VQE
                     )  # 'noisysimulation' For simulation mode
# egm = Errorgnomarker(chip_name="Baihua", result_get='hardware')  # For real hardware mode

# Step 3: Run Diagnostics and Benchmarking
results, filepath = egm.egm_run()

# Step 4: Visualize Results
egm.draw_visual_table(filepath=filepath)  # Draw the visual table for selected metrics
egm.plot_visual_figure(filepath=filepath)  # Plot the visual figures for selected metrics

# Results are saved in the `data_egm` folder, along with tables and figures if enabled.
