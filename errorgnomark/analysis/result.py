# File Path: errorgnomark/analysis/result.py
# NEW FILE: Defines a generic container for experiment results.
# This class includes a powerful .display() method for clean, object-oriented reporting.

from typing import Any, Dict, Optional
import matplotlib.pyplot as plt

class ExperimentResult:
    """
    A generic, self-contained container for experiment results.
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

        if not self.data.get('fit_successful', False):
            print("  Fit failed or was not successful. Cannot report error rates.")
        else:
            print("  Fit successful: True")
            # --- Logic to display different result types ---
            if self.name == "StandardRB":
                epc = self.data.get('epc')
                if epc is not None:
                    print(f"  --> Error Per Clifford (EPC): {epc:.4e}")

            elif self.name == "InterleavedRB":
                gate_error = self.data.get('gate_error')
                if gate_error is not None:
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