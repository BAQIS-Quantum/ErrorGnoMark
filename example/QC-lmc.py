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

# ---------------------------------------------------------
# Step 1: Define User Authentication Token
# ---------------------------------------------------------
# Register and set your actual token here (needed for hardware access)
define_token("hPjq54iTwV{DKN5z7Th5wNe.wVjVXYB8RiV{wtLfb3q/1YOzJUN5dEOvBUP2BUN5BUO4FkPjBIfmKDMjB{N7ZUN7hENhZkNuVENuVkNxJkJ7JDeimnJtBkPjxX[3WHcjxjJvOnM2SX[vRYbjClN3JUO{JENzF{NjpkJzW3d2Kzf")
# To use the actual hardware, ensure you have a valid token from your platform provider.

# ---------------------------------------------------------
# Step 2: Initialize Errorgnomarker Benchmark Object
# ---------------------------------------------------------
# You can switch between simulation and real hardware by changing result_get
mode = 'simultaneous'   # Options: 'simultaneous' or 'respective'

egm = Errorgnomarker(
    chip_name="Baihua",            # Chip name for diagnostics
    result_get='noisysimulation',  # 'hardware' for real device, 'noisysimulation' for simulation
    qubit_to_be_used=5,            # Number of qubits to use
    start_qubit=21,                # Starting qubit index
    file_path=r"./Baihua_calibration_2025-05-26 07_46_48.csv",  # Calibration file
    weights={                      # Optional: scoring weights for qubit selection
        'T1': 0.5,                 # Adjust the weight ratio for each coefficient in the calculation of qubit scores.
        'T2': 0.5,                 # This weight is used to automatically select other qubits starting from start_qubit.
        'Fidelity': 0,
        'Frequency': 0
    },
    run_all_Qubits=False,          # If True, use all qubits (overrides selection above)
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
                                   # If run_all_Qubits=False,
                                   # For MRB to run, the selected qubit indices cannot exceed 31.
                                   # If run_all_Execute=True, the fixed selection is [2,3,4,5,6,7,8,15,16,17,29,30]
    clopsqm_selected=True,         # Execute m-Qubit Speed CLOPS
    vqeqm_selected=True,           # Execute m-Qubit VQE
    Benchmarking=True,             # Enable benchmarking
    Characterization=True,         # Enable characterization
    mode=mode                      # Benchmarking mode ('simultaneous' or 'respective')
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
egm.draw_visual_table(filepath=filepath)   # Draw the visual table for selected metrics
egm.plot_visual_figure(filepath=filepath, mode=mode)  # Plot the visual figures for selected metrics

# All result data, tables, and figures are automatically saved in the './data_egm' and './figures' directories.

# ---------------------------------------------------------
# End of Example Script
# ---------------------------------------------------------

