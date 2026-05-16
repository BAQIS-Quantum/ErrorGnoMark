# File Path: errorgnomark/analysis/result.py
# [FIXED v1] - Added the missing AnalysisResult class to support tomography and other analyses.

from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt

# --- NEW CLASS: AnalysisResult ---
# This is the class that process_tomography.py is trying to import.
# It's a more general-purpose result container for analysis outputs like fidelity.

class AnalysisResult:
    """
    A structured container for the results of a data analysis routine.
    This is distinct from ExperimentResult, which may contain raw data and figures.
    """
    def __init__(self,
                 result_type: str,
                 device_name: str,
                 qubits: List[int],
                 quality_indicator: float,
                 data: Dict[str, Any]):
        """
        Args:
            result_type (str): A name for the type of result (e.g., 'process_fidelity').
            device_name (str): The name of the device or backend where the experiment ran.
            qubits (List[int]): The qubits involved in this analysis.
            quality_indicator (float): The main numerical result (e.g., fidelity, error rate).
            data (Dict[str, Any]): A dictionary containing all detailed analysis data,
                                   such as matrices, fit parameters, etc.
        """
        self.result_type = result_type
        self.device_name = device_name
        self.qubits = qubits
        self.quality_indicator = quality_indicator
        self.data = data

    def display(self):
        """
        Displays the analysis result in a structured format.
        """
        print(f"===== Analysis Result: {self.result_type} =====")
        print(f"  Device: {self.device_name}")
        print(f"  Qubits: {self.qubits}")
        
        # Customize the display based on the result type
        if 'fidelity' in self.result_type.lower():
            print(f"  -> Process Fidelity: {self.quality_indicator:.5f}")
        else:
            print(f"  -> Quality Metric: {self.quality_indicator:.5f}")
            
        if 'reconstructed_chi_matrix' in self.data:
            print("  (Detailed Chi matrix data is available in the result object's .data attribute)")
            
        print("=" * (25 + len(self.result_type)))
        print()


# --- EXISTING CLASS: ExperimentResult ---
# This class from the previous step is kept for Randomized Benchmarking.

class ExperimentResult:
    """
    A generic, self-contained container for experiment results, often including a figure.
    """
    def __init__(self, name: str, data: Dict[str, Any], figure: Optional[plt.Figure] = None):
        """
        Args:
            name: The name of the experiment (e.g., "StandardRB", "InterleavedRB").
            data: A dictionary containing all computed data and fit results.
            figure: An optional matplotlib figure object associated with the result.
        """
        self.name = name
        self.data = data
        self.figure = figure

    def display(self, title: Optional[str] = None):
        """
        Processes and displays the experiment result in a structured, readable format.
        """
        display_title = title if title else self.name
        print(f"--- Results for: '{display_title}' ---")

        if 'fit_successful' in self.data and not self.data['fit_successful']:
            print("  Fit failed or was not successful. Cannot report error rates.")
        else:
            # --- Logic to display different result types ---
            if self.name == "StandardRB":
                epc = self.data.get('epc')
                if epc is not None:
                    print("  Fit successful: True")
                    print(f"  --> Error Per Clifford (EPC): {epc:.4e}")

            elif self.name == "InterleavedRB":
                gate_error = self.data.get('gate_error')
                if gate_error is not None:
                    print("  Fit successful: True")
                    print(f"  --> Interleaved Gate Error: {gate_error:.4e}")
            else:
                # Fallback for any other experiment type
                print(f"  Data: {self.data}")

        # Display the figure if it exists
        if self.figure:
            # Set the figure title *before* showing it
            self.figure.suptitle(display_title)
            plt.show()
        else:
            print("  (No figure was generated for this result)")
        print("-" * 40 + "\n")