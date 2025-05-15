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

    def __init__(self, chip_name="Baihua", result_get='noisysimulation', qubit_to_be_used=10,
                 initial_qubit=0,
                 file_path='', weights=None):
        """
        Initializes the ErrorGnoMarker with the specified chip configuration.
        """
        super().__init__()  # Initialize the base chip class
        self.chip_name = chip_name

        if self.chip_name == "Baihua":
            self.selection_options = {
                'max_qubits_per_row': 13,
                'min_qubit_index': 0,
                'max_qubit_index': 155
            }
            self.selector = qubit_selection(
                rows=12,
                cols=13,
                qubit_index_max=155,
                qubit_to_be_used=qubit_to_be_used,
                initial_qubit=initial_qubit,
                option=self.selection_options,
                file_path=file_path,
                weights=weights
            )

        else:
            raise ValueError(f"Unsupported chip name: {self.chip_name}")

        self.result_get = result_get

        self.selection = self.selector.quselected()
        self.qubit_index_list = self.selection["qubit_index_list"]
        self.qubit_connectivity = self.selection["qubit_connectivity"]

        print("=" * 50)
        print("Selected Qubit Indices:", self.qubit_index_list)
        print("Qubit Connectivity:", self.qubit_connectivity)
        print("=" * 50)

        self.config_quality_q1gate = QualityQ1Gate(self.qubit_index_list, result_get=result_get)
        self.config_quality_q2gate = QualityQ2Gate(self.qubit_connectivity, result_get=result_get)
        self.config_quality_qmgate = QualityQmgate(self.qubit_connectivity, self.qubit_index_list, result_get=result_get)
        self.config_speed_qmgate = SpeedQmgate(self.qubit_connectivity, self.qubit_index_list, result_get=result_get)
        self.config_application_qmgate = ApplicationQmgate(self.qubit_connectivity, self.qubit_index_list, result_get=result_get)

    def egm_run(self, 
        rbq1_selected=True,
        xebq1_selected=True,
        csbq1_selected=True,
        rbq2_selected=True,
        xebq2_selected=True,
        csbq2_selected=True,
        csbq2_cnot_selected=True,
        ghzqm_selected=True,
        qvqm_selected=True,
        mrbqm_selected=True,
        clopsqm_selected=True,
        vqeqm_selected=True
        ):
        """
        Executes the EGM metrics and saves the results to a JSON file.
        Based on the selection flags, executes the relevant metric calculation.
        """
        results = {}
        total_tasks = 10  # Total tasks (metrics to be executed)
        progress_bar = tqdm(total=total_tasks, desc="Overall Progress", position=0, leave=True)

        # Start the total execution timer
        total_start_time = time.time()

        try:
            # Execute selected metrics
            if rbq1_selected:
                try:
                    results['res_egmq1_rb'] = self._run_single_qubit_rb()
                except Exception as e:
                    print(f"Error during Single Qubit RB: {e}")

            if xebq1_selected:
                try:
                    results['res_egmq1_xeb'] = self._run_single_qubit_xeb()
                except Exception as e:
                    print(f"Error during Single Qubit XEB: {e}")

            if csbq1_selected:
                try:
                    results['res_egmq1_csbp2x'] = self._run_single_qubit_csb()
                except Exception as e:
                    print(f"Error during Single Qubit CSB: {e}")

            if rbq2_selected:
                try:
                    results['res_egmq2_rb'] = self._run_two_qubit_rb()
                except Exception as e:
                    print(f"Error during Two Qubit RB: {e}")

            if xebq2_selected:
                try:
                    results['res_egmq2_xeb'] = self._run_two_qubit_xeb()
                except Exception as e:
                    print(f"Error during Two Qubit XEB: {e}")

            if csbq2_selected:
                try:
                    results['res_egmq2_csb'] = self._run_two_qubit_csb()
                except Exception as e:

                    print(f"Error during Two Qubit CSB: {e}")
            if csbq2_cnot_selected:  # Handle CNOT CSB logic
                try:
                    results['res_egmq2_csb_cnot'] = self._run_two_qubit_cnot_csb()
                except Exception as e:
                    print(f"Error during Two Qubit CNOT CSB: {e}")

            if ghzqm_selected:
                try:
                    results['res_egmqm_ghz'] = self._run_m_qubit_ghz()
                except Exception as e:
                    print(f"Error during m-Qubit GHZ Fidelity: {e}")

            if qvqm_selected:
                try:
                    results['res_egmqm_stqv'] = self._run_m_qubit_stqv()
                except Exception as e:
                    print(f"Error during m-Qubit StanQV Fidelity: {e}")

            if mrbqm_selected:
                try:
                    results['res_egmqm_mrb'] = self._run_m_qubit_mrb()
                except Exception as e:
                    print(f"Error during m-Qubit MRB Fidelity: {e}")

            if clopsqm_selected:
                try:
                    results['res_egmqm_clops'] = self._run_m_qubit_clops()
                except Exception as e:
                    print(f"Error during m-Qubit Speed CLOPS: {e}")

            if vqeqm_selected:
                try:
                    results['res_egmqm_vqe'] = self._run_m_qubit_vqe()
                except Exception as e:
                    print(f"Error during m-Qubit VQE: {e}")

        except Exception as e:
            print(f"An unexpected error occurred during execution: {e}")
        finally:
            progress_bar.close()

        # Compute and print the total execution time
        total_elapsed_time = time.time() - total_start_time
        print(f"Total execution time: {total_elapsed_time:.2f} seconds.")

        # Save results to JSON and return the filepath
        filepath = self._save_results_to_json(results)

        return results, filepath

    def _run_single_qubit_rb(self):
        start_time = time.time()
        res = self.config_quality_q1gate.q1rb()
        elapsed_time = time.time() - start_time
        print(f"Single Qubit RB completed in {elapsed_time:.2f} seconds.")
        return res

    def _run_single_qubit_xeb(self):
        start_time = time.time()
        res = self.config_quality_q1gate.q1xeb()
        elapsed_time = time.time() - start_time
        print(f"Single Qubit XEB completed in {elapsed_time:.2f} seconds.")
        return res

    def _run_single_qubit_csb(self):
        start_time = time.time()
        res = self.config_quality_q1gate.q1csb_pi_over_2_x()
        if res is None:
            print("Error: Q1CSB π/2-x task did not complete successfully.")
            return None
        elapsed_time = time.time() - start_time
        print(f"Single Qubit CSB completed in {elapsed_time:.2f} seconds.")
        return res

    def _run_two_qubit_rb(self):
        start_time = time.time()
        res = self.config_quality_q2gate.q2rb()
        elapsed_time = time.time() - start_time
        print(f"Two Qubit RB completed in {elapsed_time:.2f} seconds.")
        return res


    def _run_two_qubit_xeb(self):
        start_time = time.time()
        res = self.config_quality_q2gate.q2xeb()
        elapsed_time = time.time() - start_time
        print(f"Two Qubit XEB completed in {elapsed_time:.2f} seconds.")
        return res

    def _run_two_qubit_csb(self):
        start_time = time.time()
        res = self.config_quality_q2gate.q2csb_cz()
        elapsed_time = time.time() - start_time
        print(f"Two Qubit CSB completed in {elapsed_time:.2f} seconds.")
        return res

    def _run_two_qubit_cnot_csb(self):
        start_time = time.time()
        res = self.config_quality_q2gate.q2csb_cnot()
        elapsed_time = time.time() - start_time
        print(f"Two Qubit CNOT CSB completed in {elapsed_time:.2f} seconds.")
        return res

    def _run_m_qubit_ghz(self):
        start_time = time.time()
        res = self.config_quality_qmgate.qmghz_fidelity()
        elapsed_time = time.time() - start_time
        print(f"m-Qubit GHZ Fidelity completed in {elapsed_time:.2f} seconds.")
        return res

    def _run_m_qubit_stqv(self):
        start_time = time.time()
        res = self.config_quality_qmgate.qmstanqv()
        elapsed_time = time.time() - start_time
        print(f"m-Qubit StanQV Fidelity completed in {elapsed_time:.2f} seconds.")
        return res

    def _run_m_qubit_mrb(self):
        start_time = time.time()
        res = self.config_quality_qmgate.qmmrb()
        elapsed_time = time.time() - start_time
        print(f"m-Qubit MRB Fidelity completed in {elapsed_time:.2f} seconds.")
        return res

    def _run_m_qubit_clops(self):
        start_time = time.time()
        res = self.config_speed_qmgate.qmclops()
        elapsed_time = time.time() - start_time
        print(f"m-Qubit Speed CLOPS completed in {elapsed_time:.2f} seconds.")
        return res

    def _run_m_qubit_vqe(self):
        start_time = time.time()
        res = self.config_application_qmgate.qmVQE()
        elapsed_time = time.time() - start_time
        print(f"m-Qubit VQE completed in {elapsed_time:.2f} seconds.")
        return res

    def _save_results_to_json(self, results):
        # Create 'data_egm' folder if it does not exist
        if not os.path.exists('data_egm'):
            os.makedirs('data_egm')

        # Prepare the filename with chip name and current datetime
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.chip_name}_egm_data_{current_datetime}.json"
        filepath = os.path.join('data_egm', filename)

        # Prepare the full results dictionary with title and initial information
        full_results = {
            "title": filename,
            "chip_info": {
                "chip_name": self.chip_name,
                "rows": self.rows,
                "columns": self.columns
            },
            "qubit_index_list": self.qubit_index_list,
            "qubit_connectivity": self.qubit_connectivity,
            "results": results
        }

        # Save the full results dictionary to a JSON file
        try:
            with open(filepath, 'w') as json_file:
                json.dump(full_results, json_file, indent=4)
            print(f"EGM results saved to {filepath}")
        except Exception as e:
            print(f"Failed to save EGM results to JSON file: {e}")
        
        return filepath


    def draw_visual_table(self, *args):
        """
        Generate a table for the given metrics.
        Automatically uses the latest filepath saved.
        """
        # Retrieve the last saved filepath
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.chip_name}_egm_data_{current_datetime}.json"
        filepath = os.path.join('data_egm', filename)
        report_manager = EGMReportManager(filepath)  # Using the latest filepath
        report_manager.egm_level02_table(*args)

    def plot_visual_figure(self, *args):
        """
        Generate figures for the given metrics.
        Automatically uses the latest filepath saved.
        """
        # Retrieve the last saved filepath
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.chip_name}_egm_data_{current_datetime}.json"
        filepath = os.path.join('data_egm', filename)

        report_manager = EGMReportManager(filepath)  # Using the latest filepath
        report_manager.egm_level02_figure(*args)




from errorgnomark.token_manager import define_token, get_token
# Define your token
define_token("ROKILmIl4`zT[p8zmPZrFjYNCzS1WnI:qgFJi[m8fK5/1IO5J{OyhkOvNUO6d{OzZEO4FkPjBIfmKDMjN{N7JUN7FkNhNENuRENuVkNxJkJ7JDeimnJtBkPjxX[3WHcjxjJvOnMkGnM{mXdiKHRliYbii3ZjpkJzW3d2Kzf")

# Example usage:
if __name__ == "__main__":
    egm = Errorgnomarker(chip_name="Baihua", result_get='noisysimulation')
    # Run the EGM metrics and get results
    results = egm.egm_run(
        rbq1_selected=True,
        xebq1_selected=True,
        csbq1_selected=True,
        rbq2_selected=True,
        xebq2_selected=True,
        csbq2_selected=True,
        csbq2_cnot_selected=True,
        ghzqm_selected=True,
        qvqm_selected=True,
        mrbqm_selected=True,
        clopsqm_selected=True,
        vqeqm_selected=True
    )

    # Optionally, you can use the following methods to generate visuals after running the metrics:
    # Draw the visual table for selected metrics
    egm.draw_visual_table()

    # Plot the visual figures for selected metrics
    egm.plot_visual_figure()





