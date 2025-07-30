"""
A User Guide for Local QC Measurement & Control System
=======================================================================

This script demonstrates how to use the ErrorGnoMark software for quantum chip diagnostics and benchmarking
using the ErrorGnoMark platform in a local or simulated quantum computing environment.

If you are using a local quantum computing (QC) measurement and control system, you can access the complete
chip information online, including its topology and connectivity.

Notes:
- This example automatically defines a 12x13 BaiHua chip structure.
- The chip, qubit index list, and qubit connectivity can be customized by the user.
- To run on an actual chip, users need to register and provide a valid token.
- Real hardware execution requires registration and a valid token.
- Results, tables, and plots are saved in the 'data_egm' and 'figures' folder.
"""

# ---------------------------------------------------------
# Import Required Modules
# ---------------------------------------------------------
from errorgnomark.errorgnomarker import Errorgnomarker
from errorgnomark.token_manager import define_token, get_token
import numpy as np

# ---------------------------------------------------------
# Step 1: Define User Authentication Token
# ---------------------------------------------------------
# Register and set your actual token here (needed for hardware access)
define_token(
    "hPjq54iTwV{DKN5z7Th5wNe.wVjVXYB8RiV{wtLfb3q/1YOzJUN5dEOvBUP2BUN5BUO4FkPjBIfmKDMjB{N7ZUN7hENhZkNuVENuVkNxJkJ7JDeimnJtBkPjxX[3WHcjxjJvOnM2SX[vRYbjClN3JUO{JENzF{NjpkJzW3d2Kzf")
# To use the actual hardware, ensure you have a valid token from your platform provider.

# ---------------------------------------------------------
# Step 2: Initialize Errorgnomarker Benchmark Object
# ---------------------------------------------------------
# You can switch between simulation and real hardware by changing result_get

egm = Errorgnomarker(
    # ==================== Chip/Hardware Config ====================
    chip_name="Baihua",  # Chip name for diagnostics
    file_path=r"./Baihua_calibration_2025-05-26 07_46_48.csv",  # Calibration file
    result_get='noisysimulation',  # 'hardware' for real device, 'noisysimulation' for simulation

    # ==================== Switches & Modes =========================
    Benchmarking=True,  # Enable benchmarking
    Characterization=False,  # Enable characterization
    mode='simultaneous',  # Benchmarking mode ('simultaneous' or 'respective')
    Lightweighting=True,

    # ==================== Qubit Selection ==========================
    qubit_to_be_used=2,  # Number of qubits to use
    start_qubit=45,  # Starting qubit index
    run_all_Qubits=False,  # If True, use all qubits (overrides selection above)
    weights={  # Optional: scoring weights for qubit selection
        'T1': 0.5,  # Adjust the weight ratio for each coefficient in the calculation of qubit scores.
        'T2': 0.5,  # This weight is used to automatically select other qubits starting from start_qubit.
        'Fidelity': 0,
        'Frequency': 0},

    # ==================== Benchmarking Tasks =======================
    rbq1_selected=False,  # Execute Single Qubit RB for Q1
    xebq1_selected=True,  # Execute Single Qubit XEB for Q1

    csbq1_selected=False,  # Execute Single Qubit CSB for Q1
    ini_modes=['x', 'y', 'z'], rot_axis=None, rot_angle=np.pi / 4, hadamard='h',  # 'h'
    gate_name=None,  # 'XGate' 'YGate' 'ZGate' 'IdGate' 'WGate' 'HGate' 'SGate'
                     # Only one of Rot_axis, hadamard, and gate_name can be selected at a time.

    rbq2_selected=False,  # Execute Two Qubit RB for Q2
    xebq2_selected=False,  # Execute Two Qubit XEB for Q2
    csbq2_selected=False,  # Execute Two Qubit CSB for Q2
    csbq2_cnot_selected=False,  # Execute Two Qubit CNOT CSB
    ghzqm_selected=False,  # Execute m-Qubit GHZ Fidelity
    qvqm_selected=False,  # Execute m-Qubit StanQV Fidelity
    mrbqm_selected=False,  # Execute m-Qubit MRB Fidelity.
    # If run_all_Qubits=False,
    # For MRB to run, the selected qubit indices cannot exceed 31.
    # If run_all_Execute=True, the fixed selection is [2,3,4,5,6,7,8,15,16,17,29,30]
    clopsqm_selected=False,  # Execute m-Qubit Speed CLOPS
    vqeqm_selected=False,  # Execute m-Qubit VQE

)
# Note: For hardware run, set result_get='hardware' and ensure a valid token.

# ---------------------------------------------------------
# Step 3: Run Benchmarking & Diagnostics
# ---------------------------------------------------------
results, filepath = egm.egm_run()
# - 'results' contains diagnostic and benchmarking metrics.
# - 'filepath' points to the CSV data for further analysis and plotting.

# ---------------------------------------------------------
# Step 4: Visualization & Output
# ---------------------------------------------------------
# Visual table: highlights main results in formatted table style
egm.draw_visual_table(filepath=filepath)  # Draw the visual table for selected metrics
egm.plot_visual_figure(filepath=filepath, mode='simultaneous')  # Plot the visual figures for selected metrics

# All result data, tables, and figures are automatically saved in the './data_egm' and './figures' directories.

# ---------------------------------------------------------
# End of Example Script
# ---------------------------------------------------------
