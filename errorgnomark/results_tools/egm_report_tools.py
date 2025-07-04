# Standard library imports
import os  # For operating system-related functionalities
import json  # For working with JSON data
from datetime import datetime  # For handling date and time
import sys
import numpy as np

# Third-party imports
import matplotlib.pyplot as plt  # For creating visualizations
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']  # matplotlib自带
plt.rcParams['axes.unicode_minus'] = False


# ErrorGnoMark-specific imports
from errorgnomark.results_tools.visualization import VisualPlot  # For generating visual plots

class EGMReportManager:
    """
    This class handles the reading of EGM JSON data files and generates 
    text-based tables for various benchmarking metrics. It also saves the 
    tables as text files in designated directories.
    """

    def __init__(self, json_file_path):
        """
        Initialize the EGMReportManager class and load JSON data.

        Args:
            json_file_path (str): Path to the JSON data file.
        """
        self.json_file_path = json_file_path
        self.data = self._read_json()
        self.results = self.data.get("results", {})
        self.qubit_index_list = self.data.get("qubit_index_list", [])
        self.qubit_connectivity = self.data.get("qubit_connectivity", [])
        self.output_dir = "tables"  # Directory for saving tables
        self.figures_dir = "figures"  # Directory for saving figures
        self._create_output_dir()
        self._create_figures_dir()

    def _read_json(self):
        """
        Read the JSON data file.

        Returns:
            dict: The JSON data.
        """
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            print(f"Successfully read JSON data from {self.json_file_path}")
            return data
        except Exception as e:
            print(f"Failed to read JSON file: {e}")
            raise e

    def _create_output_dir(self):
        """
        Create the directory for saving tables if it doesn't exist.
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created directory '{self.output_dir}' for saving tables.")
        else:
            print(f"Directory '{self.output_dir}' already exists.")

    def _create_figures_dir(self):
        """
        Create the directory for saving figures if it doesn't exist.
        """
        if not os.path.exists(self.figures_dir):
            os.makedirs(self.figures_dir)
            print(f"Created directory '{self.figures_dir}' for saving figures.")

    def format_title(self, metric_name):
        """
        Format the title by converting variable names to a readable format.

        Args:
            metric_name (str): Original metric name.

        Returns:
            str: Formatted title.
        """
        if metric_name.startswith("res_egmq1_"):
            formatted = "EGM_q1_" + metric_name[len("res_egmq1_"):].upper()
        elif metric_name.startswith("res_egmq2_"):
            formatted = "EGM_q2_" + metric_name[len("res_egmq2_"):].upper()
        elif metric_name.startswith("res_egmqm_"):
            formatted = "EGM_MultiQubit_" + metric_name[len("res_egmqm_"):].upper()
        else:
            formatted = metric_name.replace("_", " ").title()
        return formatted

    def _calculate_col_widths(self, column_names, data):
        """
        Calculate column widths based on column names and data content.
        
        Args:
            column_names (list): List of column names.
            data (list of lists): Table data.
        
        Returns:
            list: List of column widths.
        """
        # Ensure data rows have the same number of columns as column names
        for row in data:
            if len(row) != len(column_names):
                print(f"Warning: Row {row} has a different number of columns than the header.")
                row = row[:len(column_names)]  # Trim any extra columns
                row.extend([""] * (len(column_names) - len(row)))  # Pad with empty strings if necessary
        
        # Now calculate the column widths
        col_widths = []
        for i, col in enumerate(column_names):
            max_content_width = max(len(str(row[i])) for row in data) if data else 0
            col_width = max(len(col), max_content_width)
            col_widths.append(col_width)
        return col_widths


    def _build_border(self, left, middle, right, col_widths):
        """
        Build a table border.

        Args:
            left (str): Left border character.
            middle (str): Middle connection character.
            right (str): Right border character.
            col_widths (list): List of column widths.

        Returns:
            str: Constructed border string.
        """
        border = left
        for i, width in enumerate(col_widths):
            border += '─' * width
            if i < len(col_widths) - 1:
                border += middle
            else:
                border += right
        border += '\n'
        return border

    def _build_row(self, row, col_widths):
        """
        Build a row for the table.

        Args:
            row (list): Data for the row.
            col_widths (list): List of column widths.

        Returns:
            str: Constructed row string.
        """
        row_str = '│'
        for i, cell in enumerate(row):
            cell_content = str(cell)
            cell_str = f"{cell_content.center(col_widths[i])}"
            row_str += cell_str + '│'
        row_str += '\n'
        return row_str

    def _draw_table_text(self, title, column_names, data, output_filename):
        """
        Create a text-based table and save it to a file.

        Args:
            title (str): Table title.
            column_names (list): List of column names.
            data (list of lists): Table data.
            output_filename (str): Output file name.

        Returns:
            str: Table as a string.
        """
        col_widths = self._calculate_col_widths(column_names, data)
        top_border = self._build_border('┌', '┬', '┐', col_widths)
        header_border = self._build_border('├', '┼', '┤', col_widths)
        bottom_border = self._build_border('└', '┴', '┘', col_widths)
        header = self._build_row(column_names, col_widths)
        data_lines = ''.join(self._build_row(row, col_widths) for row in data)
        table_width = sum(col_widths) + len(col_widths) + 1
        title_formatted = title.center(table_width) + '\n'
        indent = ' ' * 8

        full_table = f"{indent}{title_formatted}{indent}{top_border}{indent}{header}{indent}{header_border}"
        for line in data_lines.splitlines():
            full_table += f"{indent}{line}\n"
        full_table += f"{indent}{bottom_border}"

        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_table)
        print(f"Table '{title}' saved as '{output_path}'.")
        return full_table

    def _format_table(self, column_names, data):
        """
        Format the table data as a string.

        Args:
            column_names (list): The column headers of the table.
            data (list): The data rows of the table.

        Returns:
            str: The formatted table as a string.
        """
        # Ensure padding for rows with missing data or trimming extra data
        for row in data:
            if len(row) < len(column_names):
                print(f"Warning: Row {row} has a different number of columns than the header.")
                row.extend([""] * (len(column_names) - len(row)))  # Pad missing columns
            elif len(row) > len(column_names):
                print(f"Warning: Row {row} has more columns than the header.")
                row = row[:len(column_names)]  # Trim extra columns

        # Calculate column widths
        col_widths = self._calculate_col_widths(column_names, data)

        # Construct the table borders and rows
        top_border = self._build_border('┌', '┬', '┐', col_widths)
        header = self._build_row(column_names, col_widths)
        separator = self._build_border('├', '┼', '┤', col_widths)
        data_rows = ''.join(self._build_row(row, col_widths) for row in data)
        bottom_border = self._build_border('└', '┴', '┘', col_widths)

        # Combine all parts to form the full table
        table = f"{top_border}{header}{separator}{data_rows}{bottom_border}"
        return table

    def draw_res_egmq1_rb(self):
        """
        Draws a table for the res_egmq1_rb metric.
        """
        metric_name = "res_egmq1_rb"
        metric_data = self.results.get(metric_name, {})
        if not metric_data:
            print(f"No data found for {metric_name}.")
            return

        data = []
        for q_idx in self.qubit_index_list:
            error_rate = metric_data.get(f"qubit_{q_idx}", {}).get("error_rate", "N/A")
            formatted_error_rate = f"{error_rate:.4f}" if isinstance(error_rate, float) else error_rate
            data.append([str(q_idx), formatted_error_rate])

        column_names = ["Qubit", "Error Rate"]
        title = self.format_title(metric_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{metric_name}_{timestamp}.txt"

        self._draw_table_text(title, column_names, data, output_filename)

    def draw_res_egmq1_xeb(self):
        """
        Draws a table for the res_egmq1_xeb metric.
        """
        metric_name = "res_egmq1_xeb"
        metric_data = self.results.get(metric_name, {})
        hardware_data = metric_data.get("hardware", [])
        if not hardware_data:
            print(f"No hardware data found for {metric_name}.")
            return

        # Draw according to the order of qubit_index_list
        data = []
        for q_idx, infidelity in zip(self.qubit_index_list, hardware_data):
            formatted_infidelity = f"{infidelity:.4f}" if isinstance(infidelity, float) else infidelity
            data.append([str(q_idx), formatted_infidelity])

        column_names = ["Qubit", "Infid XEB"]
        title = self.format_title(metric_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{metric_name}_{timestamp}.txt"

        self._draw_table_text(title, column_names, data, output_filename)

    def draw_res_egmq1_csbp2x(self):
        """
        Draws a table for the res_egmq1_csbp2x metric.
        """
        metric_name = "res_egmq1_csbp2x"
        metric_data = self.results.get(metric_name, {})
        if not metric_data:
            print(f"No data found for {metric_name}.")
            return

        # Extract process_infidelities, stochastic_infidelities, angle_errors
        process_infidelities = metric_data.get("process_infidelities", [])
        stochastic_infidelities = metric_data.get("stochastic_infidelities", [])
        angle_errors = metric_data.get("angle_errors", [])

        # Draw according to the order of qubit_index_list
        data = []
        for q_idx in self.qubit_index_list:
            proc_inf = process_infidelities[q_idx] if q_idx < len(process_infidelities) else "N/A"
            sto_inf = stochastic_infidelities[q_idx] if q_idx < len(stochastic_infidelities) else "N/A"
            angle_err = angle_errors[q_idx] if q_idx < len(angle_errors) else "N/A"

            # Format values to 4 decimal places
            formatted_proc_inf = f"{proc_inf:.4f}" if isinstance(proc_inf, float) else proc_inf
            formatted_sto_inf = f"{sto_inf:.4f}" if isinstance(sto_inf, float) else sto_inf
            formatted_angle_err = f"{angle_err:.4f}" if isinstance(angle_err, float) else angle_err

            data.append([str(q_idx), formatted_proc_inf, formatted_sto_inf, formatted_angle_err])

        column_names = ["Qubit", "Process Infid", "Stotistic Infid", "Angle Error"]
        title = self.format_title(metric_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{metric_name}_{timestamp}.txt"

        self._draw_table_text(title, column_names, data, output_filename)

    def draw_res_egmq2_rb(self):
        """
        Draws a table for the res_egmq2_rb metric.
        """
        metric_name = "res_egmq2_rb"
        metric_data = self.results.get(metric_name, {})
        if not metric_data:
            print(f"No data found for {metric_name}.")
            return

        data = []
        for pair in self.qubit_connectivity:
            key = f"[{pair[0]}, {pair[1]}]"
            error_rate = metric_data.get(key, {}).get("error_rate", "N/A")
            formatted_error_rate = f"{error_rate:.4f}" if isinstance(error_rate, float) else error_rate
            display_pair = f"({pair[0]},{pair[1]})"
            data.append([display_pair, formatted_error_rate])

        # Add average error rate
        average_error_rate = metric_data.get("average_error_rate", "N/A")
        formatted_average_error_rate = f"{average_error_rate:.4f}" if isinstance(average_error_rate, float) else average_error_rate
        data.append(["Average", formatted_average_error_rate])

        column_names = ["Qubits", "Error Rate"]
        title = self.format_title(metric_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{metric_name}_{timestamp}.txt"

        self._draw_table_text(title, column_names, data, output_filename)

    def draw_res_egmq2_xeb(self):
        """
        Draws a table for the res_egmq2_xeb metric.
        """
        metric_name = "res_egmq2_xeb"
        metric_data = self.results.get(metric_name, {})
        hardware_data = metric_data.get("hardware", [])
        if not hardware_data:
            print(f"No hardware data found for {metric_name}.")
            return

        data = []
        for pair, infidelity in zip(self.qubit_connectivity, hardware_data):
            pair_str = f"({pair[0]},{pair[1]})"
            formatted_infidelity = f"{infidelity:.4f}" if isinstance(infidelity, float) else infidelity
            data.append([pair_str, formatted_infidelity])

        column_names = ["Qubits", "Infid XEB"]
        title = self.format_title(metric_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{metric_name}_{timestamp}.txt"

        self._draw_table_text(title, column_names, data, output_filename)

    def draw_res_egmq2_csb_cz(self):
        """
        Draws a table for the res_egmq2_csb_cz metric.
        """
        metric_name = "res_egmq2_csb_cz"
        metric_data = self.results.get(metric_name, {})
        qubit_pairs_results = metric_data.get("qubit_pairs_results", [])
        if not qubit_pairs_results:
            print(f"No qubit pairs results found for {metric_name}.")
            return

        data = []
        for pair, result in zip(self.qubit_connectivity, qubit_pairs_results):
            process_infidelity = result.get("process_infidelity", "N/A")
            stochastic_infidelity = result.get("stochastic_infidelity", "N/A")
            theta_error = result.get("theta_error", "N/A")
            phi_error = result.get("phi_error", "N/A")

            # Format values to 4 decimal places
            formatted_process_infidelity = f"{process_infidelity:.4f}" if isinstance(process_infidelity, float) else process_infidelity
            formatted_stochastic_infidelity = f"{stochastic_infidelity:.4f}" if isinstance(stochastic_infidelity, float) else stochastic_infidelity
            formatted_theta_error = f"{theta_error:.4f}" if isinstance(theta_error, float) else theta_error
            formatted_phi_error = f"{phi_error:.4f}" if isinstance(phi_error, float) else phi_error

            # Format qubit pair as (x,y)
            pair_str = f"({pair[0]},{pair[1]})"

            data.append([pair_str, formatted_process_infidelity, formatted_stochastic_infidelity, formatted_theta_error, formatted_phi_error])

        column_names = ["Qubits", "Process Infid", "CSB_S", "CSB_T", "CSB_A"]
        title = self.format_title(metric_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{metric_name}_{timestamp}.txt"

        self._draw_table_text(title, column_names, data, output_filename)

    def draw_res_egmq2_csb_cnot(self):
        """
        Draws a table for the res_egmq2_csb_cnot metric.
        """
        metric_name = "res_egmq2_csb_cnot"
        metric_data = self.results.get(metric_name, {})
        qubit_pairs_results = metric_data.get("qubit_pairs_results", [])
        if not qubit_pairs_results:
            print(f"No qubit pairs results found for {metric_name}.")
            return

        data = []
        for pair, result in zip(self.qubit_connectivity, qubit_pairs_results):
            process_infidelity = result.get("process_infidelity", "N/A")
            stochastic_infidelity = result.get("stochastic_infidelity", "N/A")
            theta_error = result.get("theta_error", "N/A")
            phi_error = result.get("phi_error", "N/A")

            # Format values to 4 decimal places if they are floats
            formatted_process_infidelity = f"{process_infidelity:.4f}" if isinstance(process_infidelity, float) else process_infidelity
            formatted_stochastic_infidelity = f"{stochastic_infidelity:.4f}" if isinstance(stochastic_infidelity, float) else stochastic_infidelity
            formatted_theta_error = f"{theta_error:.4f}" if isinstance(theta_error, float) else theta_error
            formatted_phi_error = f"{phi_error:.4f}" if isinstance(phi_error, float) else phi_error

            # Format qubit pair as (x,y)
            pair_str = f"({pair[0]},{pair[1]})"

            data.append([pair_str, formatted_process_infidelity, formatted_stochastic_infidelity, formatted_theta_error, formatted_phi_error])

        column_names = ["Qubits", "Process Infid", "CSB_S", "CSB_T", "CSB_A"]
        title = self.format_title(metric_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{metric_name}_{timestamp}.txt"

        self._draw_table_text(title, column_names, data, output_filename)

    def draw_res_egmqm_ghz(self):
        """
        Draw a table for the metric res_egmqm_ghz.
        """
        metric_name = "res_egmqm_ghz"
        metric_data = self.results.get(metric_name, {})
        if not metric_data:
            print(f"No data found for {metric_name}.")
            return

        fidelity_list = metric_data.get("fidelity", [])
        if len(fidelity_list) != 6:
            print(f"Unexpected number of fidelity entries for {metric_name}. Expected 6, got {len(fidelity_list)}.")
            return

        nqubits = [3, 4, 5, 6, 7, 8]
        data = []
        for nq, fid in zip(nqubits, fidelity_list):
            formatted_fid = f"{fid:.4f}" if isinstance(fid, float) else fid
            data.append([str(nq), formatted_fid])

        column_names = ["NQUBITS", "FIDELITY_GHZ"]
        title = self.format_title(metric_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{metric_name}_{timestamp}.txt"

        self._draw_table_text(title, column_names, data, output_filename)

    def draw_res_egmqm_stqv(self):
        """
        Build a Multi-Qubit Gates Quality - Quantum Volume table.
        Returns the generated table string and the maximum Quantum Volume value.
        """
        metric_name_stqv = "res_egmqm_stqv"
        metric_data_stqv = self.results.get(metric_name_stqv, {})

        if not metric_data_stqv:
            print(f"No data found for {metric_name_stqv}.")
            return "N/A", None

        # Dynamically extract nqubits and quantum_volume data
        nqubits_data = []
        qv_data = []

        for key, value in metric_data_stqv.items():
            nqubits = value.get("total_qubits")
            qv = value.get("quantum_volume")

            # Filter out entries where quantum_volume is None or 0
            if nqubits is not None and qv is not None:
                nqubits_data.append(nqubits)
                qv_data.append(qv)

        if not nqubits_data or not qv_data:
            print(f"Incomplete or invalid data for {metric_name_stqv}.")
            return "N/A", None

        # Ensure data is sorted by nqubits
        sorted_data = sorted(zip(nqubits_data, qv_data), key=lambda x: x[0])
        nqubits_data, qv_data = zip(*sorted_data)

        # Dynamically generate table content
        max_qv = max(qv_data) if qv_data else None
        nqubits_row = ["NQubits"] + [str(nq) for nq in nqubits_data]
        qv_row = ["Quantum Volume"] + [str(int(qv)) for qv in qv_data]  # Ensure integers are displayed

        # Calculate column widths
        col_widths = [max(len(str(nq)), len(str(qv))) for nq, qv in zip(nqubits_row, qv_row)]

        # Construct the table
        top_border = self._build_border('┌', '┬', '┐', col_widths)
        header_row = self._build_row(nqubits_row, col_widths)
        separator = self._build_border('├', '┼', '┤', col_widths)
        qv_data_row = self._build_row(qv_row, col_widths)
        bottom_border = self._build_border('└', '┴', '┘', col_widths)

        table = f"{top_border}{header_row}{separator}{qv_data_row}{bottom_border}"

        return table, max_qv

    def draw_res_egmqm_mrb(self):
        """
        Draw a table for the metric res_egmqm_mrb and return the table string.
        """
        metric_name = "res_egmqm_mrb"
        
        # Access the data for the specific metric
        metric_data = self.results.get(metric_name, None)

        if not metric_data:
            print(f"No data found for {metric_name}.")
            return ""

        polarizations = metric_data.get('polarizations', [])
        qubits_for_length = metric_data.get('qubits_for_length', {})

        if not polarizations or not qubits_for_length:
            print(f"Missing data for {metric_name}: 'polarizations' or 'qubits_for_length'.")
            return ""

        # Get the unique lengths across all qubit groups
        unique_lengths = sorted(set(length for qubit_group in qubits_for_length.values()
                                    for length in qubit_group.keys()))

        column_names = ["Qubit Count", "Qubits"] + [f"Length {length}" for length in unique_lengths]

        data = []
        
        # Iterate over each qubit group in qubits_for_length
        for qubit_count, lengths in sorted(qubits_for_length.items()):
            qubits = lengths.get(unique_lengths[0], [])
            row = [str(qubit_count), ', '.join(map(str, qubits))]

            for length in unique_lengths:
                length_index = unique_lengths.index(length)
                polarization_value = polarizations[int(qubit_count) // 2 - 1][length_index]  # Fetch the correct polarization
                row.append(f"{polarization_value:.4f}")

            data.append(row)

        title = self.format_title("res_egmqm_mrb")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"res_egmqm_mrb_{timestamp}.txt"

        table_str = self._draw_table_text(title, column_names, data, output_filename)

        return table_str

    def generate_chip_layout(self):
        """
        Generate a textual layout of the chip, where qubit positions are represented by dots
        and selected qubits are connected by short lines.
        
        Returns:
            str: A textual representation of the chip layout.
        """
        # Initialize an empty 2D grid representing the chip
        rows = self.data["chip_info"]["rows"]
        columns = self.data["chip_info"]["columns"]
        chip_grid = [["." for _ in range(columns)] for _ in range(rows)]
        
        # Mark the selected qubits with short lines
        for idx in self.qubit_index_list:
            row, col = idx // columns, idx % columns
            chip_grid[row][col] = "Q"  # Mark selected qubits with "Q"
        
        # Create the layout as a string
        chip_layout = ""
        for row in chip_grid:
            chip_layout += " ".join(row) + "\n"
        
        return chip_layout

    def generate_all_tables(self):
        """
        Generate all benchmarking tables.
        """
        self.draw_res_egmq1_rb()
        self.draw_res_egmq1_xeb()
        self.draw_res_egmq1_csbp2x()
        self.draw_res_egmq2_rb()
        self.draw_res_egmq2_xeb()
        self.draw_res_egmq2_csb_cz()
        self.draw_res_egmq2_csb_cnot()
        self.draw_res_egmqm_ghz()
        self.draw_res_egmqm_stqv()
        self.draw_res_egmqm_mrb()

    def egm_level02_table(self,        
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
        Generates a comprehensive Level02 report that includes information on 
        Single-Qubit Gate Quality, Two-Qubit Gate Quality, Multi-Qubit Gates Quality,
        CLOPS, and VQE results. The report title is based on the JSON data file name.
        """

        # selecteds for each specific section (set to True by default, you can set them to False to skip sections)
        # Get the JSON file name
        file_name = os.path.basename(self.json_file_path)

        # Initialize the report string
        report = ""

        # Main title for the report
        main_title = "Errorgnomark Report of 'QXX' Chip"
        report += f"{main_title.center(80)}\n"
        report += "=" * 80 + "\n\n"
        
        # Chip Structure and Selected Qubit Indices
        chip_info = self.data.get("chip_info", {})
        if not chip_info:
            print("Chip information is missing from the JSON data.")
            return
        report += f"Chip Structure: {chip_info.get('rows', 'N/A')} rows x {chip_info.get('columns', 'N/A')} columns\n"
        report += "-" * 50 + "\n"
        report += f"Selected Qubit Indices: {str(self.qubit_index_list)}\n"
        report += f"Qubit Connectivity: {str(self.qubit_connectivity)}\n"
        report += "=" * 80 + "\n\n"

        # Generate and display the chip layout with selected qubits
        chip_layout = self.generate_chip_layout()
        report += "Chip Structure Layout:\n"
        report += chip_layout + "\n"

        # Define column names for different categories
        single_q_columns = ["Qubit", "RB", "XEB"]
        csb_single_q_columns = ["Qubit", "CSB_P", "CSB_S", "CSB_A"]
        two_q_columns = ["Qubits", "RB", "XEB"]
        csb_two_q_columns = ["Qubits", "CSB_P", "CSB_S", "CSB_T", "CSB_A"]
        multi_q_columns_ghz = ["NQUBITS", "FIDELITY_GHZ"]

        # Section 1: Single-Qubit Gate Quality - RB
        if rbq1_selected:
            report += "## Section 1: Single-Qubit Gate Quality - RB\n"
            report += "-" * 50 + "\n"
            report += "**Randomized Benchmarking (RB)**: Measures gate error rates.\n"
            report += "**Cross-Entropy Benchmarking (XEB)**: Evaluates gate fidelity.\n\n"
            
            # Build Single-Qubit Gate Quality data (RB)
            single_q_data = []
            for q_idx in self.qubit_index_list:
                rb = self.results.get("res_egmq1_rb", {}).get(f"qubit_{q_idx}", {}).get("error_rate", "N/A")
                rb = f"{rb:.4f}" if isinstance(rb, float) else rb
                single_q_data.append([str(q_idx), rb, "N/A"])  # XEB column as "N/A" temporarily for this section

            report += self._format_table(single_q_columns, single_q_data) + "\n\n"

        # Section 2: Single-Qubit Gate Quality - XEB
        if xebq1_selected:
            report += "## Section 2: Single-Qubit Gate Quality - XEB\n"
            report += "-" * 50 + "\n"
            report += "**Cross-Entropy Benchmarking (XEB)**: Evaluates gate fidelity.\n\n"

            # Build Single-Qubit Gate Quality data (XEB)
            single_q_data = []
            for q_idx in self.qubit_index_list:
                xeb = self.results.get("res_egmq1_xeb", {}).get("hardware", [])
                xeb = f"{xeb[q_idx]:.4f}" if isinstance(xeb, list) and q_idx < len(xeb) and isinstance(xeb[q_idx], float) else "N/A"
                single_q_data.append([str(q_idx), "N/A", xeb])  # RB column as "N/A" temporarily for this section

            report += self._format_table(single_q_columns, single_q_data) + "\n\n"

        # Section 3: Single-Qubit Gate Quality - CSB
        if csbq1_selected:
            report += "## Section 3: Single-Qubit Gate Quality - CSB (pi/2 - X)\n"
            report += "-" * 50 + "\n"
            report += "**Channel Spectrum Benchmarking (CSB)**: Measures process, stochastic, and angle error rates for qubit operations.\n"
            report += "**CSB_P**: Process Infidelity\n"
            report += "**CSB_S**: Stochastic Infidelity\n"
            report += "**CSB_A**: Angle Error\n\n"

            # Build CSB (pi/2 - X) results for Single-Qubits (CSB_P, CSB_S, CSB_A)
            csb_single_q_data = []
            for q_idx in self.qubit_index_list:
                csb_p = self.results.get("res_egmq1_csbp2x", {}).get("process_infidelities", [])
                csb_s = self.results.get("res_egmq1_csbp2x", {}).get("stochastic_infidelities", [])
                csb_a = self.results.get("res_egmq1_csbp2x", {}).get("angle_errors", [])

                csb_p = f"{csb_p[q_idx]:.4f}" if isinstance(csb_p, list) and q_idx < len(csb_p) and isinstance(csb_p[q_idx], float) else "N/A"
                csb_s = f"{csb_s[q_idx]:.4f}" if isinstance(csb_s, list) and q_idx < len(csb_s) and isinstance(csb_s[q_idx], float) else "N/A"
                csb_a = f"{csb_a[q_idx]:.4f}" if isinstance(csb_a, list) and q_idx < len(csb_a) and isinstance(csb_a[q_idx], float) else "N/A"

                csb_single_q_data.append([str(q_idx), csb_p, csb_s, csb_a])

            report += self._format_table(csb_single_q_columns, csb_single_q_data) + "\n\n"

        # Section 4: Two-Qubit Gate Quality - RB
        if rbq2_selected:
            report += "## Section 4: Two-Qubit Gate Quality - RB\n"
            report += "-" * 50 + "\n"
            report += "**Randomized Benchmarking (RB)**: Measures gate error rates for two qubits.\n\n"
            
            # Build Two-Qubit Gate Quality data (RB)
            two_q_data = []
            for pair in self.qubit_connectivity:
                x, y = pair
                qubits = f"({x},{y})"
                rb = self.results.get("res_egmq2_rb", {}).get(f"[{x}, {y}]", {}).get("error_rate", "N/A")
                rb = f"{rb:.4f}" if isinstance(rb, float) else rb
                two_q_data.append([qubits, rb, "N/A"])  # XEB column as "N/A" temporarily for this section

            report += self._format_table(two_q_columns, two_q_data) + "\n\n"

        # Section 5: Two-Qubit Gate Quality - XEB
        if xebq2_selected:
            report += "## Section 5: Two-Qubit Gate Quality - XEB\n"
            report += "-" * 50 + "\n"
            report += "**Cross-Entropy Benchmarking (XEB)**: Evaluates two-qubit gate fidelity.\n\n"

            # Build Two-Qubit Gate Quality data (XEB)
            two_q_data = []
            for pair in self.qubit_connectivity:
                x, y = pair
                qubits = f"({x},{y})"
                xeb_list = self.results.get("res_egmq2_xeb", {}).get("hardware", [])
                index = self.qubit_connectivity.index(pair)
                xeb = f"{xeb_list[index]:.4f}" if isinstance(xeb_list, list) and index < len(xeb_list) and isinstance(xeb_list[index], float) else "N/A"
                two_q_data.append([qubits, "N/A", xeb])  # RB column as "N/A" temporarily for this section

            report += self._format_table(two_q_columns, two_q_data) + "\n\n"

        # Section 6: Two-Qubit Gate Quality - CSB
        if csbq2_selected:
            report += "## Section 6: Two-Qubit Gate Quality - CSB\n"
            report += "-" * 50 + "\n"
            report += "**Channel Spectrum Benchmarking (CSB)**: Evaluates process, stochastic, and angle errors for qubit pairs.\n\n"

            # Build CSB results for Two-Qubits (CSB_P, CSB_S, CSB_T, CSB_A)
            csb_two_q_data = []
            for pair in self.qubit_connectivity:
                x, y = pair
                csb_p = self.results.get("res_egmq2_csb_cz", {}).get("qubit_pairs_results", [])
                index = self.qubit_connectivity.index(pair)
                if index < len(csb_p):
                    process_infid = csb_p[index].get("process_infidelity", "N/A")
                    stochastic_infid = csb_p[index].get("stochastic_infidelity", "N/A")
                    theta_error = csb_p[index].get("theta_error", "N/A")
                    phi_error = csb_p[index].get("phi_error", "N/A")

                    csb_two_q_data.append([f"({x},{y})", process_infid, stochastic_infid, theta_error, phi_error])
                else:
                    csb_two_q_data.append([f"({x},{y})", "N/A", "N/A", "N/A", "N/A"])

            report += self._format_table(csb_two_q_columns, csb_two_q_data) + "\n\n"

        # Section 7: CNOT CSB Errors (Moved here)
        if csbq2_cnot_selected:  # Add this section for CNOT CSB errors
            report += "## Section 7: CNOT Gate Quality - CSB\n"
            report += "-" * 50 + "\n"
            report += "**Channel Spectrum Benchmarking (CSB)**: Evaluates process, stochastic, and angle errors for CNOT qubit pairs.\n\n"

            # Build CSB results for CNOT (CSB_P, CSB_S, CSB_T, CSB_A)
            csb_cnot_data = []
            for pair in self.qubit_connectivity:
                x, y = pair
                csb_p = self.results.get("res_egmq2_csb_cnot", {}).get("qubit_pairs_results", [])
                index = self.qubit_connectivity.index(pair)
                if index < len(csb_p):
                    process_infid = csb_p[index].get("process_infidelity", "N/A")
                    stochastic_infid = csb_p[index].get("stochastic_infidelity", "N/A")
                    theta_error = csb_p[index].get("theta_error", "N/A")
                    phi_error = csb_p[index].get("phi_error", "N/A")

                    csb_cnot_data.append([f"({x},{y})", process_infid, stochastic_infid, theta_error, phi_error])
                else:
                    csb_cnot_data.append([f"({x},{y})", "N/A", "N/A", "N/A", "N/A"])

            report += self._format_table(csb_two_q_columns, csb_cnot_data) + "\n\n"

        # Section 8: Multi-Qubit Gate Quality - GHZ Fidelity
        if ghzqm_selected:
            report += "## Section 7: Multi-Qubit Gates Quality - Fidelity GHZ\n"
            report += "-" * 50 + "\n"
            report += "**N-Qubit GHZ state fidelity**: Measures the fidelity of GHZ states on multiple qubits.\n\n"

            # Build Multi-Qubit Gates Quality - Fidelity_GHZ data
            multi_q_data_ghz = []
            metric_name_ghz = "res_egmqm_ghz"
            metric_data_ghz = self.results.get(metric_name_ghz, {})
            fidelity_list = metric_data_ghz.get("fidelity", [])
            if len(fidelity_list) == 6:
                nqubits_ghz = [3, 4, 5, 6, 7, 8]
                for nq, fid in zip(nqubits_ghz, fidelity_list):
                    formatted_fid = f"{fid:.4f}" if isinstance(fid, float) else fid
                    multi_q_data_ghz.append([str(nq), formatted_fid])

            report += self._format_table(multi_q_columns_ghz, multi_q_data_ghz) + "\n\n"

        # Section 9: Quantum Volume
        if qvqm_selected:
            report += "## Section 8: Multi-Qubit Gates Quality - Quantum Volume\n"
            report += "-" * 50 + "\n"
            report += "**Quantum Volume**: Measures the complexity of quantum circuits that a quantum computer can process.\n\n"
            
            # Dynamically extract Quantum Volume data from res_egmqm_stqv
            quantum_volume_data = {}
            for key, value in self.results.get("res_egmqm_stqv", {}).items():
                nqubits = key.split('_')[-1]  # Extract qubit count from the key like 'nqubits_nqubits_2'
                quantum_volume_data[nqubits] = value.get("quantum_volume", 0)

            if quantum_volume_data:  # Only proceed if data is available
                # Calculate Maximum Quantum Volume
                max_quantum_volume = max(quantum_volume_data.values())

                # Prepare data for the quantum volume table
                quantum_volume_columns = ["NQubits"] + list(quantum_volume_data.keys())
                quantum_volume_values = ["Quantum Volume"] + [str(quantum_volume_data[q]) for q in quantum_volume_data]

                # Use _format_table to create the table with proper formatting
                table = self._format_table(quantum_volume_columns, [quantum_volume_values])

                # Add the quantum volume table to the report
                report += table
                report += f"\nMaximum Quantum Volume: {max_quantum_volume}\n\n"
            else:
                report += "**Quantum Volume data is missing or incomplete. Skipping this section.**\n\n"

        # Section 10: MRB
        if mrbqm_selected:
            report += "## Section 9: Multi-Qubit Gates Quality - MRB\n"
            report += "-" * 50 + "\n"
            report += "**Multi-Qubit Randomized Benchmarking (MRB)**: Measures multi-qubit gate error rates for different qubit lengths.\n\n"

            # Build MRB results for Multi-Qubits (Length 12, 4, 8)
            mrb_data = []
            mrb_results = self.results.get("res_egmqm_mrb", {}).get("qubits_for_length", {})

            # Dynamically get the available lengths from the data (lengths 4, 8, and 12)
            available_lengths = sorted(set(int(length) for qubit_count in mrb_results.values() for length in qubit_count.keys()))

            # Get polarizations for error rates
            polarizations = self.results.get("res_egmqm_mrb", {}).get("polarizations", [])

            # Loop through each qubit count and associated lengths
            for qubit_count, lengths in mrb_results.items():
                # Initialize row for this qubit_count
                row = [str(qubit_count), ", ".join(map(str, lengths.get("12", [])))]

                # For each length in the available lengths, get the corresponding error rate
                for length in available_lengths:
                    # Ensure that the length exists in the list of qubits for this qubit count
                    if str(length) in lengths:
                        # Check if there are enough entries in polarizations for this length
                        if length - 4 < len(polarizations[0]):  # Ensure polarization data is available for this length
                            error_rate = polarizations[0][length - 4]  # Access the error rate from polarizations
                            row.append(f"{error_rate:.4f}")
                        else:
                            row.append("N/A")
                    else:
                        row.append("N/A")
                
                # Now append the row to the mrb_data
                mrb_data.append(row)

            # Define the table headers
            mrb_columns = ["Qubit Count", "Qubits"] + [f"Length {length}" for length in available_lengths]

            # Format the table output (you can format it into a readable structure or use the `self._format_table` method)
            report += self._format_table(mrb_columns, mrb_data) + "\n\n"

        # Section 11: CLOPS
        if clopsqm_selected:
            clops = self.results.get("res_egmqm_clops", {}).get("CLOPSQM", "N/A")

            # Check if 'clops' is a valid number (float or int). If it's not, use "N/A".
            if clops != "N/A":
                try:
                    # Try to convert 'clops' to a float and format it in scientific notation
                    clops = float(clops)
                    report += f"CLOPS: {clops:.4e}\n"
                except ValueError:
                    # If 'clops' is not a valid number, print "N/A"
                    report += f"CLOPS: N/A\n"
            else:
                # If 'clops' is "N/A", simply display "N/A"
                report += f"CLOPS: N/A\n"

        # Section 12: VQE
        if vqeqm_selected:
            vqe = self.results.get("res_egmqm_vqe", {})
            vqe_problem = vqe.get("Problem Description", "N/A")
            final_energy = vqe.get("Final Energy", "N/A")
            report += "\n## Section 12: Multi-Qubit Gates Application\n" + "-" * 50 + "\n"
            report += f"VQE Problem: {vqe_problem}\n"
            report += f"Final Energy: {final_energy}\n"

        # Save the report to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"level02_report_{timestamp}.txt"
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Level02 report saved as '{output_path}'.")

       

    def _save_figure(self, figure, filepath):
        """
        Save a figure to the specified filepath.

        Args:
            figure: The matplotlib figure to be saved.
            filepath (str): The file path to save the figure.
        """
        try:
            figure.savefig(filepath)
            print(f"Figure saved to {filepath}")
        except Exception as e:
            print(f"Failed to save figure: {e}")
        finally:
            # Close the figure after saving it to avoid memory issues
            plt.close(figure)

    def egm_level02_figure(self,
                           rbq1_selected=False,
                           xebq1_selected=False,
                           csbq1_selected=False,
                           rbq2_selected=False,
                           xebq2_selected=False,
                           csbq2_selected=False,
                           csbq2_cnot_selected=False,  # Add new parameter for CSBQ2_CNOT plot
                           ghzqm_selected=False,       # New parameter for CSBQ2_CZ plot
                           qvqm_selected=False,
                           mrbqm_selected=False,
                           clopsqm_selected=False,
                           vqeqm_selected=False,
                           mode='respective'
                           ):
        """
        Generate visualizations for metrics and save them as images based on selected options.
        """

        # selected options for each figure (set to True by default, you can set them to False to skip specific plots)
        visualizer = VisualPlot(self.json_file_path)

        # Define output file paths
        rbq1_path = os.path.join(self.figures_dir, "RBQ1_Heatmap.png")
        xebq1_path = os.path.join(self.figures_dir, "XEBQ1_Heatmap.png")
        csbq1_path = os.path.join(self.figures_dir, "CSBQ1_Heatmap.png")
        rbq2_path = os.path.join(self.figures_dir, "RBQ2_Heatmap.png")
        xebq2_path = os.path.join(self.figures_dir, "XEBQ2_Heatmap.png")
        csbq2_cz_path = os.path.join(self.figures_dir, "CSBQ2_CZ_Heatmap.png")  # Path for CSBQ2_CZ plot
        csbq2_cnot_path = os.path.join(self.figures_dir, "CSBQ2_CNOT_Heatmap.png")  # Path for CSBQ2_CNOT plot
        mrbqm_path = os.path.join(self.figures_dir, "MRBQM_Heatmap.png")
        ghzqm_path = os.path.join(self.figures_dir, "GHZQM_Fidelity.png")  # Path for GHZ fidelity plot

        # Generate and save the plots based on the selected options
        if rbq1_selected:
            visualizer.plot_rbq1(grid_size=(12, 13), mode=mode, path=rbq1_path)
            # plt.savefig(rbq1_path)
            # plt.close()

        if xebq1_selected:
            visualizer.plot_xebq1(grid_size=(12, 13), mode=mode, path=xebq1_path)
            # plt.savefig(xebq1_path)
            # plt.close()

        if csbq1_selected:
            visualizer.plot_csbq1(grid_size=(12, 13), mode=mode, path=xebq1_path)
            # plt.savefig(csbq1_path)
            # plt.close()

        if rbq2_selected:
            visualizer.plot_rbq2()
            plt.savefig(rbq2_path)
            plt.close()

        if xebq2_selected:
            visualizer.plot_xebq2()
            plt.savefig(xebq2_path)
            plt.close()

        # Generate and save the CSBQ2_CZ plot if selected
        if csbq2_selected:  # Check if the CSBQ2_CZ plot is selected
            visualizer.plot_csbq2_cz()  # Call the CSBQ2_CZ plot function
            plt.savefig(csbq2_cz_path)  # Save the plot as a PNG file
            plt.close()

        # Generate and save the CSBQ2_CNOT plot if selected
        if csbq2_cnot_selected:  # Check if the CSBQ2_CNOT plot is selected
            visualizer.plot_csbq2_cnot()  # Call the CSBQ2_CNOT plot function
            plt.savefig(csbq2_cnot_path)  # Save the plot as a PNG file
            plt.close()

        if mrbqm_selected:
            visualizer.plot_mrbqm()
            plt.savefig(mrbqm_path)
            plt.close()

        # Generate and save the GHZ fidelity plot if selected
        if ghzqm_selected:  # Check if the GHZ plot is selected
            visualizer.plot_ghzqm_fidelity()  # Call the GHZ fidelity plot function
            plt.savefig(ghzqm_path)  # Save the plot as a PNG file
            plt.close()


