# Standard library imports
import json  # For handling JSON data
import os  # For file and directory management
import sys  # For system-specific parameters and functions
import time  # For timing operations
from datetime import datetime  # For handling date and time

# Third-party library imports
from requests.exceptions import RequestException, ReadTimeout  # For HTTP requests and error handling
from tqdm import tqdm  # For progress bar visualization

# Local imports
from errorgnomark.cirpulse_generator.qubit_selector import qubit_selection, chip  # For qubit selection and chip setup
from errorgnomark.configuration import (  # For various quality and benchmarking configurations
    QualityQ1Gate,
    QualityQ2Gate,
    QualityQmgate,
    SpeedQmgate,
    ApplicationQmgate
)
from errorgnomark.results_tools.egm_report_tools import EGMReportManager  # For generating reports


class Errorgnomarker(chip):
    """
    Retrieves error and performance metrics for qubits and quantum gates at various levels.
    Supports single-qubit, two-qubit, multi-qubit gates, and application-level tests.
    """

    def __init__(self, chip_name="QXX",result_get= 'noisysimulation'):
        """
        Initializes the ErrorGnoMarker with the specified chip configuration.

        Parameters:
            chip_name (str): Name of the chip configuration.
        """
        super().__init__()  # Initialize the base chip class

        self.chip_name = chip_name

        if self.chip_name == "QXX":
            # Initialize the chip with specific rows and columns
            self.rows = 10
            self.columns = 10
        else:
            # Handle other chip configurations if necessary
            raise ValueError(f"Unsupported chip name: {self.chip_name}")
        
        self.result_get = result_get
        # Step 1: Define selection options
        self.selection_options = {
            'max_qubits_per_row': 9,
            'min_qubit_index': 0,
            'max_qubit_index': 50
        }

        # Step 2: Initialize qubit selection with constraints
        self.selector = qubit_selection(
            chip=self,
            qubit_index_max=50,
            qubit_number=9,
            option=self.selection_options
        )

        # Perform qubit selection
        self.selection = self.selector.quselected()
        self.qubit_index_list = self.selection["qubit_index_list"]
        self.qubit_connectivity = self.selection["qubit_connectivity"]

        print("=" * 50)
        print("Selected Qubit Indices:", self.qubit_index_list)
        print("Qubit Connectivity:", self.qubit_connectivity)
        print("=" * 50)

        # Initialize configuration objects with the selected qubits and connectivity

        self.config_quality_q1gate = QualityQ1Gate(self.qubit_index_list, result_get=result_get)
        self.config_quality_q2gate = QualityQ2Gate(self.qubit_connectivity, result_get=result_get)
        self.config_quality_qmgate = QualityQmgate(self.qubit_connectivity, self.qubit_index_list, result_get=result_get)
        self.config_speed_qmgate = SpeedQmgate(self.qubit_connectivity, self.qubit_index_list, result_get=result_get)
        self.config_application_qmgate = ApplicationQmgate(self.qubit_connectivity, self.qubit_index_list, result_get=result_get)

    def egm_run(self, egm_level='level_2', visual_table=None, visual_figure=None):
        """
        Executes the EGM metrics and saves the results to a JSON file.

        Parameters:
            egm_level (str): Level of detail ('level_0', 'level_1', 'level_2').
            visual_table (bool): If True, generate the level02 table.
            visual_figure (bool): If True, generate the level02 figures.
        """
        results = {}
        total_tasks = 10  # Total tasks (metrics to be executed)
        progress_bar = tqdm(total=total_tasks, desc="Overall Progress", position=0, leave=True)

        try:
            # Single Qubit RB
            print("[Running] Single Qubit RB...")
            res_egmq1_rb = self.config_quality_q1gate.q1rb()
            if res_egmq1_rb is None:
                raise ValueError("q1rb returned None")
            results['res_egmq1_rb'] = res_egmq1_rb
            progress_bar.update(1)

            # Single Qubit XEB
            print("[Running] Single Qubit XEB...")
            res_egmq1_xeb = self.config_quality_q1gate.q1xeb()
            if res_egmq1_xeb is None:
                raise ValueError("q1xeb returned None")
            results['res_egmq1_xeb'] = res_egmq1_xeb
            progress_bar.update(1)

            # Single Qubit CSB
            print("[Running] Single Qubit CSB...")
            res_egmq1_csbp2x = self.config_quality_q1gate.q1csb_pi_over_2_x()
            if res_egmq1_csbp2x is None:
                raise ValueError("q1csb_pi_over_2_x returned None")
            results['res_egmq1_csbp2x'] = res_egmq1_csbp2x
            progress_bar.update(1)

            # Two Qubit RB
            print("[Running] Two Qubit RB...")
            res_egmq2_rb = self.config_quality_q2gate.q2rb()
            if res_egmq2_rb is None:
                raise ValueError("q2rb returned None")
            results['res_egmq2_rb'] = res_egmq2_rb
            progress_bar.update(1)

            # Two Qubit XEB
            print("[Running] Two Qubit XEB...")
            res_egmq2_xeb = self.config_quality_q2gate.q2xeb()
            if res_egmq2_xeb is None:
                raise ValueError("q2xeb returned None")
            results['res_egmq2_xeb'] = res_egmq2_xeb
            progress_bar.update(1)

            # Two Qubit CSB
            print("[Running] Two Qubit CSB_CZ...")
            res_egmq2_csb_cz = self.config_quality_q2gate.q2csb_cz()
            if res_egmq2_csb_cz is None:
                raise ValueError("q2csb_cz returned None")
            results['res_egmq2_csb_cz'] = res_egmq2_csb_cz
            progress_bar.update(1)

            # m-Qubit GHZ Fidelity
            print("[Running] m-Qubit GHZ Fidelity...")
            res_egmqm_ghz = self.config_quality_qmgate.qmghz_fidelity()
            if res_egmqm_ghz is None:
                raise ValueError("qmghz_fidelity returned None")
            results['res_egmqm_ghz'] = res_egmqm_ghz
            progress_bar.update(1)

            # m-Qubit StanQV Fidelity
            print("[Running] m-Qubit StanQV Fidelity...")
            res_egmqm_stqv = self.config_quality_qmgate.qmstanqv()
            if res_egmqm_stqv is None:
                raise ValueError("qmstanqv returned None")
            results['res_egmqm_stqv'] = res_egmqm_stqv
            progress_bar.update(1)

            # m-Qubit MRB Fidelity
            print("[Running] m-Qubit MRB Fidelity...")
            res_egmqm_mrb = self.config_quality_qmgate.qmmrb()
            if res_egmqm_mrb is None:
                raise ValueError("qmmrb returned None")
            results['res_egmqm_mrb'] = res_egmqm_mrb
            progress_bar.update(1)

            # m-Qubit Speed CLOPS
            print("[Running] m-Qubit Speed CLOPS...")
            res_egmqm_clops = self.config_speed_qmgate.qmclops()
            if res_egmqm_clops is None:
                raise ValueError("qmclops returned None")
            results['res_egmqm_clops'] = res_egmqm_clops
            progress_bar.update(1)

            # m-Qubit VQE
            print("[Running] m-Qubit VQE...")
            res_egmqm_vqe = self.config_application_qmgate.qmVQE()
            if res_egmqm_vqe is None:
                raise ValueError("qmVQE returned None")
            results['res_egmqm_vqe'] = res_egmqm_vqe
            progress_bar.update(1)

        except Exception as e:
            print(f"An error occurred during execution: {e}")
        finally:
            progress_bar.close()

        # Prepare the filename with chip name and current datetime
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.chip_name}_egm_data_{current_datetime}.json"
        



# Example usage:
if __name__ == "__main__":
    egm = Errorgnomarker(chip_name="QXX")
    egm.egm_run(visual_table=True, visual_figure=True)
