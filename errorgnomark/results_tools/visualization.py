import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm, colors as mcolors
import matplotlib.patches as patches
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']  # matplotlib自带
plt.rcParams['axes.unicode_minus'] = False

from mpl_toolkits.axes_grid1 import make_axes_locatable

class VisualPlot:
    def __init__(self, file_path):
        """
        Initialize the VisualPlot class.
        Parameters:
            file_path (str): Path to the JSON file containing benchmarking results.
        """
        self.file_path = file_path
        self.data = self._load_data()

    def _load_data(self):
        """
        Load data from the JSON file.
        Returns:
            dict: Parsed JSON data.
        """
        with open(self.file_path, "r") as f:
            return json.load(f)

    def plot_heatmap_with_spacing(self, grid, title, colorbar_label, cmap='viridis', save_path=None):
        """
        Create a heatmap with grid spacing to visualize benchmarking data, with cell values displayed.
        Parameters:
            grid (ndarray): Heatmap data as a 2D NumPy array.
            title (str): Title of the heatmap.
            colorbar_label (str): Label for the colorbar.
            cmap (str): Colormap for the heatmap (default: 'viridis').
            save_path (str, optional): Path to save the figure as a PNG file. If None, the figure is not saved.
        """
        fig, ax = plt.subplots(figsize=(16, 10))

        # Mask the grid where there is no data (np.nan)
        masked_grid = np.ma.masked_where(np.isnan(grid), grid)

        # Plot the heatmap with masked data (no data will not be shown)
        im = ax.imshow(masked_grid, cmap=cmap, interpolation='nearest')

        # Add white grid lines between cells
        for i in range(grid.shape[0] + 1):
            ax.axhline(i - 0.5, color='white', linewidth=1.5)
            ax.axvline(i - 0.5, color='white', linewidth=1.5)

        # Remove empty rows and columns
        valid_rows = np.any(~np.isnan(grid), axis=1)
        valid_cols = np.any(~np.isnan(grid), axis=0)

        # Only show the valid portion of the grid
        ax.set_xlim(np.where(valid_cols)[0][0] - 0.5, np.where(valid_cols)[0][-1] + 0.5)
        ax.set_ylim(np.where(valid_rows)[0][0] - 0.5, np.where(valid_rows)[0][-1] + 0.5)

        # Remove the ticks and labels for the empty regions
        ax.set_xticks(np.where(valid_cols)[0])
        ax.set_yticks(np.where(valid_rows)[0])

        # Update the labels to reflect the valid data range
        ax.set_xticklabels(np.arange(np.sum(valid_cols)))
        ax.set_yticklabels(np.arange(np.sum(valid_rows)))

        ax.set_title(title)
        ax.set_xlabel("Column")
        ax.set_ylabel("Row")

        # Display the values in each grid cell with 3 decimal places
        for row in range(grid.shape[0]):
            for col in range(grid.shape[1]):
                if not np.isnan(grid[row, col]):  # Skip NaN values
                    ax.text(col, row, f'{grid[row, col]:.3f}', ha='center', va='center', color='white', fontsize=10)

        # Create the colorbar to match the figure height
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)

        # Set color bar based on the grid values
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=np.nanmin(grid), vmax=np.nanmax(grid)))
        sm.set_array([])  # Create an empty array for the ScalarMappable
        cbar = fig.colorbar(sm, cax=cax)
        cbar.set_label(colorbar_label, rotation=270, labelpad=20)

        # Adjust the layout to ensure the color bar fits correctly and maintains its height
        plt.tight_layout()

        # Save the figure if save_path is provided
        if save_path:
            plt.savefig(save_path, dpi=300)  # Save with high resolution
            print(f"Figure saved as {save_path}")

        # Show the plot
        # plt.show()



    def plot_rbq1(self, grid_size=(12, 13)):
        """
        Generate a heatmap for single-qubit Randomized Benchmarking (RB) error rates.
        Parameters:
            grid_size (tuple): Fixed dimensions of the grid (default: (12, 13)).
        """
        rows, cols = grid_size

        # Create the grid dynamically based on the number of qubits
        num_qubits = len(self.data["results"]["res_egmq1_rb"])  # Get number of qubits
        grid_rows = (num_qubits // cols) + (1 if num_qubits % cols else 0)  # Calculate grid rows dynamically

        # Create an empty grid to store the error rates, initialized to NaN
        grid = np.full((rows, cols), np.nan)  # Using np.nan to indicate empty/unused slots

        # Loop through the qubits and fill the grid with their error rates
        rb_data = self.data["results"]["res_egmq1_rb"]

        for qubit_index, values in rb_data.items():
            qubit_index = int(qubit_index.split('_')[-1])  # Get the qubit index from the string

            # Calculate the row and column for this qubit (fit within a 12x13 grid)
            row = qubit_index // cols  # Row is based on index divided by the number of columns
            col = qubit_index % cols  # Column is the remainder

            # Ensure we don't try to write outside the grid (shouldn't happen with the fixed 12x13 grid)
            if row < rows and col < cols:
                grid[row, col] = values["error_rate"]
            else:
                print(f"Warning: Qubit {qubit_index} exceeds grid size, skipping.")

        # Plot the heatmap
        self.plot_heatmap_with_spacing(grid, "Rbq1 Heatmap", "Error Rate", cmap='viridis')

    def plot_xebq1(self, grid_size=(12, 13)):
        """
        Generate a heatmap for single-qubit Cross-Entropy Benchmarking (XEB) error rates.
        Parameters:
            grid_size (tuple): Fixed dimensions of the grid (default: (12, 13)).
        """
        rows, cols = grid_size

        # Create an empty grid to store the error rates, initialized to NaN
        grid = np.full((rows, cols), np.nan)  # Using np.nan to indicate empty/unused slots

        # Get XEB data, handle case where data might be missing
        xeb_data = self.data["results"].get("res_egmq1_xeb", {}).get("hardware", [])

        for qubit_index, xeb_value in enumerate(xeb_data):
            # Calculate the row and column for this qubit (fit within a 12x13 grid)
            row = qubit_index // cols  # Row is based on index divided by the number of columns
            col = qubit_index % cols  # Column is the remainder

            # Ensure we don't try to write outside the grid (shouldn't happen with the fixed 12x13 grid)
            if row < rows and col < cols:
                grid[row, col] = xeb_value
            else:
                print(f"Warning: Qubit {qubit_index} exceeds grid size, skipping.")

        # Plot the heatmap
        self.plot_heatmap_with_spacing(grid, "Xebq1 Heatmap", "XEB Value", cmap='viridis')


    def plot_csbq1(self, grid_size=(12, 13)):
        """
        Generate heatmaps for single-qubit CSB metrics, including process infidelities, 
        stochastic infidelities, and angle errors.
        Parameters:
            grid_size (tuple): Fixed dimensions of the grid (default: (12, 13)).
        """
        rows, cols = grid_size
        csb_data = self.data["results"]["res_egmq1_csbp2x"]
        process_infidelities = csb_data["process_infidelities"]
        stochastic_infidelities = csb_data["stochastic_infidelities"]
        angle_errors = csb_data["angle_errors"]

        # Create empty grids for the different metrics, initialized to NaN
        process_grid = np.full((rows, cols), np.nan)
        stochastic_grid = np.full((rows, cols), np.nan)
        angle_grid = np.full((rows, cols), np.nan)

        for i, (p_val, s_val, a_val) in enumerate(zip(process_infidelities, stochastic_infidelities, angle_errors)):
            row = i // cols
            col = i % cols
            process_grid[row, col] = p_val
            stochastic_grid[row, col] = s_val
            angle_grid[row, col] = a_val

        # Plot the heatmaps for each metric
        self.plot_heatmap_with_spacing(process_grid, "Csbq1 Process Infidelities Heatmap", "Process Infidelity", cmap='viridis')
        self.plot_heatmap_with_spacing(stochastic_grid, "Csbq1 Stochastic Infidelities Heatmap", "Stochastic Infidelity", cmap='viridis')
        self.plot_heatmap_with_spacing(angle_grid, "Csbq1 Angle Errors Heatmap", "Angle Error", cmap='viridis')


    def plot_rbq2(self):
        chip_info = self.data["chip_info"]
        rows = chip_info["rows"]
        cols = chip_info["columns"]
        rb_data = self.data["results"]["res_egmq2_rb"]

        norm = mcolors.Normalize(vmin=-0.02, vmax=0.04)
        cmap = cm.get_cmap("viridis")

        # 自动找出使用的 qubit 区域
        used_rows = [qubit // cols for pair in rb_data if pair != "average_error_rate" for qubit in eval(pair)]
        used_cols = [qubit % cols for pair in rb_data if pair != "average_error_rate" for qubit in eval(pair)]

        min_row, max_row = max(min(used_rows) - 1, 0), min(max(used_rows) + 1, rows - 1)
        min_col, max_col = max(min(used_cols) - 1, 0), min(max(used_cols) + 1, cols)

        fig, ax = plt.subplots(figsize=(16, 10))
        ax.set_aspect('equal')

        # 设置主图坐标轴
        ax.set_xticks(np.arange(min_col, max_col + 1))
        ax.set_yticks(np.arange(min_row, max_row + 1))
        ax.set_xticklabels(np.arange(min_col, max_col + 1))
        ax.set_yticklabels(np.arange(min_row, max_row + 1))
        ax.set_xticks(np.arange(min_col, max_col + 1) - 0.5, minor=True)
        ax.set_yticks(np.arange(min_row, max_row + 1) - 0.5, minor=True)
        ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)

        hex_width = 0.3
        for pair, values in rb_data.items():
            if pair == "average_error_rate":
                continue

            # Check if the error rate is None or null
            error_rate = values.get("error_rate")
            if error_rate is None:
                continue  # Skip this pair if error_rate is None or invalid

            qubit_1, qubit_2 = eval(pair)
            row_1, col_1 = qubit_1 // cols, qubit_1 % cols
            row_2, col_2 = qubit_2 // cols, qubit_2 % cols
            x_center = (col_1 + col_2) / 2
            y_center = (row_1 + row_2) / 2

            hexagon = patches.RegularPolygon(
                (x_center, y_center),
                numVertices=6,
                radius=hex_width,
                orientation=np.pi / 6,
                facecolor=cmap(norm(error_rate)),  # 仅设置填充色
                edgecolor='black',  # 单独设置边框
                lw=2
            )
            ax.add_patch(hexagon)
            ax.text(x_center, y_center, f'{error_rate:.3f}',
                    color='white', ha='center', va='center', fontsize=7)

        ax.set_xlim(min_col - 0.5, max_col + 0.5)
        ax.set_ylim(min_row - 0.5, max_row + 0.5)
        ax.set_title("Two-Qubit Gate Error Rates", fontsize=16)
        ax.set_xlabel("Column", fontsize=14)
        ax.set_ylabel("Row", fontsize=14)

        # ✅ 使用 make_axes_locatable 保证 colorbar 高度与主图一致
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="3%", pad=0.1)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cax)
        cbar.set_label("Error Rate", rotation=270, labelpad=20)

        plt.tight_layout()
        # plt.show()


    def plot_xebq2(self):
        """
        Generate a heatmap for two-qubit Cross-Entropy Benchmarking (XEB) error rates.
        The grid is fixed as 12x13, representing the chip layout.
        """
        qubit_pairs = self.data["qubit_connectivity"]
        xeb_data = self.data["results"]["res_egmq2_xeb"]["hardware"]

        # Filter out any null or None data
        filtered = [(pair, val) for pair, val in zip(qubit_pairs, xeb_data) if val is not None]

        rows, cols = 12, 13  # Fixed grid layout for the chip (12x13)

        # Find the actual used coordinates (rows, cols)
        used_rows = [q // cols for pair, _ in filtered for q in pair]
        used_cols = [q % cols for pair, _ in filtered for q in pair]

        # Define the min and max row and column limits based on used data
        min_row, max_row = max(min(used_rows) - 1, 0), min(max(used_rows) + 1, rows - 1)
        min_col, max_col = max(min(used_cols) - 1, 0), min(max(used_cols) + 1, cols - 1)

        # Define colormap and normalization
        norm = mcolors.Normalize(vmin=0, vmax=1)  # Adjust the range as needed based on the data
        cmap = cm.get_cmap("viridis")  # Use a perceptually uniform colormap

        fig, ax = plt.subplots(figsize=(16, 10))
        ax.set_aspect('equal')

        # Set the axis ticks and labels based on the fixed grid size
        ax.set_xticks(np.arange(0, cols, 1))
        ax.set_yticks(np.arange(0, rows, 1))
        ax.set_xticklabels(np.arange(0, cols, 1))
        ax.set_yticklabels(np.arange(0, rows, 1))
        ax.set_xticks(np.arange(0, cols, 1) - 0.5, minor=True)
        ax.set_yticks(np.arange(0, rows, 1) - 0.5, minor=True)
        ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)

        # Plot hexagons for each pair
        hex_width = 0.3
        for (qubit_1, qubit_2), value in filtered:
            try:
                # Ensure value is a float (if it's not, convert it)
                process_infidelity = float(value)  # Ensure correct extraction of the value
            except (TypeError, ValueError):
                # Skip if the value is not a valid number
                continue

            row_1, col_1 = qubit_1 // cols, qubit_1 % cols
            row_2, col_2 = qubit_2 // cols, qubit_2 % cols
            x_center = (col_1 + col_2) / 2
            y_center = (row_1 + row_2) / 2

            # Create a hexagon and add it to the plot
            hexagon = patches.RegularPolygon(
                (x_center, y_center),
                numVertices=6,
                radius=hex_width,
                orientation=np.pi / 6,
                facecolor=cmap(norm(process_infidelity)),  # 仅设置填充色
                edgecolor='black',  # 单独设置边框
                lw=2
            )
            ax.add_patch(hexagon)
            ax.text(x_center, y_center, f'{process_infidelity:.3f}',
                    color='white', ha='center', va='center', fontsize=7)

        ax.set_xlim(-0.5, cols - 0.5)
        ax.set_ylim(-0.5, rows - 0.5)
        ax.set_title("XEB Error Rates", fontsize=16)
        ax.set_xlabel("Column", fontsize=14)
        ax.set_ylabel("Row", fontsize=14)

        # Use make_axes_locatable to ensure colorbar height matches the figure height
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="3%", pad=0.1)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cax)
        cbar.set_label("Error Rate", rotation=270, labelpad=20)

        plt.tight_layout()
        # plt.show()




    def plot_csbq2_cz(self):
        """
        Generate a heatmap for two-qubit CSB (Controlled-Z Gate) error rates.
        The grid is fixed as 12x13, representing the chip layout.
        """
        chip_info = self.data["chip_info"]
        rows = chip_info["rows"]  # 12
        cols = chip_info["columns"]  # 13
        qubit_pairs = self.data["qubit_connectivity"]
        csb_data = self.data["results"]["res_egmq2_csb"]["qubit_pairs_results"]  # CSB data for CZ gate

        # Filter out any null or None data
        filtered = [(pair, val) for pair, val in zip(qubit_pairs, csb_data) if val is not None]

        # Find the actual used coordinates (rows, cols)
        used_rows = [q // cols for pair, _ in filtered for q in pair]
        used_cols = [q % cols for pair, _ in filtered for q in pair]

        # Define the min and max row and column limits based on used data
        min_row, max_row = max(min(used_rows) - 1, 0), min(max(used_rows) + 1, rows - 1)
        min_col, max_col = max(min(used_cols) - 1, 0), min(max(used_cols) + 1, cols - 1)

        norm = mcolors.Normalize(vmin=0, vmax=1)  # Normalize the data values for color mapping
        cmap = cm.get_cmap("viridis")  # Use a perceptually uniform colormap

        fig, ax = plt.subplots(figsize=(16, 10))
        ax.set_aspect('equal')

        # Set the axis ticks and labels based on the valid rows and columns
        ax.set_xticks(np.arange(min_col, max_col + 1))
        ax.set_yticks(np.arange(min_row, max_row + 1))
        ax.set_xticklabels(np.arange(min_col, max_col + 1))
        ax.set_yticklabels(np.arange(min_row, max_row + 1))
        ax.set_xticks(np.arange(min_col, max_col + 1) - 0.5, minor=True)
        ax.set_yticks(np.arange(min_row, max_row + 1) - 0.5, minor=True)
        ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)

        # Plot hexagons for each pair
        hex_width = 0.3
        for (qubit_1, qubit_2), value in filtered:
            try:
                # Ensure value is a float (if it's not, convert it)
                process_infidelity = float(value["process_infidelity"])  # Ensure correct extraction of the value
            except (TypeError, ValueError):
                # Skip if the value is not a valid number
                continue

            row_1, col_1 = qubit_1 // cols, qubit_1 % cols
            row_2, col_2 = qubit_2 // cols, qubit_2 % cols
            x_center = (col_1 + col_2) / 2
            y_center = (row_1 + row_2) / 2

            # Create a hexagon and add it to the plot
            hexagon = patches.RegularPolygon(
                (x_center, y_center),
                numVertices=6,
                radius=hex_width,
                orientation=np.pi / 6,
                facecolor=cmap(norm(process_infidelity)),  # 仅设置填充色
                edgecolor='black',  # 单独设置边框
                lw=2
            )
            ax.add_patch(hexagon)
            ax.text(x_center, y_center, f'{process_infidelity:.3f}',
                    color='white', ha='center', va='center', fontsize=7)

        ax.set_xlim(min_col - 0.5, max_col + 0.5)
        ax.set_ylim(min_row - 0.5, max_row + 0.5)
        ax.set_title("CZ Gate Error Rates (CSB)", fontsize=16)
        ax.set_xlabel("Column", fontsize=14)
        ax.set_ylabel("Row", fontsize=14)

        # Use make_axes_locatable to ensure colorbar height matches the figure height
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="3%", pad=0.1)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cax)
        cbar.set_label("Error Rate", rotation=270, labelpad=20)

        plt.tight_layout()
        # plt.show()

    def plot_csbq2_cnot(self):
        """
        Generate a heatmap for two-qubit CSB (Controlled-NOT Gate) error rates.
        The grid is fixed as 12x13, representing the chip layout.
        """
        chip_info = self.data["chip_info"]
        rows = chip_info["rows"]  # 12
        cols = chip_info["columns"]  # 13
        qubit_pairs = self.data["qubit_connectivity"]
        csb_data = self.data["results"]["res_egmq2_csb_cnot"]["qubit_pairs_results"]  # CSB data for CNOT gate

        # Filter out any null or None data
        filtered = [(pair, val) for pair, val in zip(qubit_pairs, csb_data) if val is not None]

        # Find the actual used coordinates (rows, cols)
        used_rows = [q // cols for pair, _ in filtered for q in pair]
        used_cols = [q % cols for pair, _ in filtered for q in pair]

        # Define the min and max row and column limits based on used data
        min_row, max_row = max(min(used_rows) - 1, 0), min(max(used_rows) + 1, rows - 1)
        min_col, max_col = max(min(used_cols) - 1, 0), min(max(used_cols) + 1, cols - 1)

        norm = mcolors.Normalize(vmin=0, vmax=1)  # Normalize the data values for color mapping
        cmap = cm.get_cmap("viridis")  # Use a perceptually uniform colormap

        fig, ax = plt.subplots(figsize=(16, 10))
        ax.set_aspect('equal')

        # Set the axis ticks and labels based on the valid rows and columns
        ax.set_xticks(np.arange(min_col, max_col + 1))
        ax.set_yticks(np.arange(min_row, max_row + 1))
        ax.set_xticklabels(np.arange(min_col, max_col + 1))
        ax.set_yticklabels(np.arange(min_row, max_row + 1))
        ax.set_xticks(np.arange(min_col, max_col + 1) - 0.5, minor=True)
        ax.set_yticks(np.arange(min_row, max_row + 1) - 0.5, minor=True)
        ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)

        # Plot hexagons for each pair
        hex_width = 0.3
        for (qubit_1, qubit_2), value in filtered:
            try:
                # Ensure value is a float (if it's not, convert it)
                process_infidelity = float(value["process_infidelity"])  # Ensure correct extraction of the value
            except (TypeError, ValueError):
                # Skip if the value is not a valid number
                continue

            row_1, col_1 = qubit_1 // cols, qubit_1 % cols
            row_2, col_2 = qubit_2 // cols, qubit_2 % cols
            x_center = (col_1 + col_2) / 2
            y_center = (row_1 + row_2) / 2

            # Create a hexagon and add it to the plot
            hexagon = patches.RegularPolygon(
                (x_center, y_center),
                numVertices=6,
                radius=hex_width,
                orientation=np.pi / 6,
                facecolor=cmap(norm(process_infidelity)),  # 仅设置填充色
                edgecolor='black',  # 单独设置边框
                lw=2
            )
            ax.add_patch(hexagon)
            ax.text(x_center, y_center, f'{process_infidelity:.3f}',
                    color='white', ha='center', va='center', fontsize=7)

        ax.set_xlim(min_col - 0.5, max_col + 0.5)
        ax.set_ylim(min_row - 0.5, max_row + 0.5)
        ax.set_title("CNOT Gate Error Rates (CSB)", fontsize=16)
        ax.set_xlabel("Column", fontsize=14)
        ax.set_ylabel("Row", fontsize=14)

        # Use make_axes_locatable to ensure colorbar height matches the figure height
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="3%", pad=0.1)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cax)
        cbar.set_label("Error Rate", rotation=270, labelpad=20)

        plt.tight_layout()
        # plt.show()

    def plot_ghzqm_fidelity(self):
        """
        Plot GHZ state fidelity for different qubit counts (3, 4, 5, 6, 7, 8).
        """
        # Extract fidelity data from the 'res_egmqm_ghz' key
        ghz_fidelity = self.data['results']['res_egmqm_ghz']['fidelity']
        qubit_indices = self.data['results']['res_egmqm_ghz']['qubit_index']
        
        # Quibit counts we're interested in
        qubit_counts = [3, 4, 5, 6, 7, 8]

        # Interpolate fidelity values for each qubit count
        fidelity_values = []
        for count in qubit_counts:
            # Find the closest matching qubit index in the data
            if count - 3 < len(ghz_fidelity):
                fidelity_values.append(ghz_fidelity[count - 3])
            else:
                fidelity_values.append(np.nan)

        # Plotting
        plt.figure(figsize=(8, 6))
        plt.plot(qubit_counts, fidelity_values, marker='o', linestyle='-', color='b', label='GHZ Fidelity')

        # Adding labels and title
        plt.title('GHZ State Fidelity vs Qubit Count', fontsize=16)
        plt.xlabel('Qubit Count', fontsize=14)
        plt.ylabel('Fidelity', fontsize=14)
        plt.grid(True)
        plt.xticks(qubit_counts)
        plt.yticks(np.linspace(0, 1, 11))

        # Show legend
        plt.legend()

        # Display the plot
        plt.tight_layout()
        # plt.show()
        
    def plot_mrbqm(self):
        """
        Generate a heatmap for the MRB (polarization) values.
        This heatmap will plot qubit counts (2, 4, 6, 8) on the x-axis,
        lengths (4, 8, 12) on the y-axis, and polarization values as color intensity.
        """
        # Extract polarization and qubits_for_length from the data
        polarizations = self.data["results"]["res_egmqm_mrb"]["polarizations"]
        qubits_for_length = self.data["results"]["res_egmqm_mrb"]["qubits_for_length"]

        # Get the unique lengths available in the data
        unique_lengths = sorted(set(length for qubit_group in qubits_for_length.values()
                                    for length in qubit_group.keys()))

        # Create a matrix to store the polarization values (rows: lengths, columns: qubit counts)
        grid = np.zeros((len(unique_lengths), len(qubits_for_length)))

        # Iterate over each qubit count and the corresponding lengths
        for i, qubit_count in enumerate(sorted(qubits_for_length.keys())):
            # Get the corresponding qubits for the current qubit_count
            for j, length in enumerate(unique_lengths):
                # Get the polarization value for the given qubit_count and length
                polarization_value = polarizations[i][j]
                grid[j, i] = polarization_value  # Store the value in the matrix

        # Plot the heatmap
        self.plot_heatmap_with_spacing(grid, "MRBQM Heatmap (Polarization)", "Polarization", cmap='Blues')
