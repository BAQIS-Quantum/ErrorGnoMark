class chip:
    """
    Represents a quantum chip with a 2D grid of qubits.

    This class provides the basic structure of a quantum chip, 
    defined by the number of rows and columns. It serves as 
    the foundation for qubit selection and connectivity in a 
    quantum system.

    Attributes:
        rows (int): Number of rows in the chip grid.
        columns (int): Number of columns in the chip grid.
    """

    def __init__(self, rows=12, columns=13):
        self.rows = rows
        self.columns = columns


class qubit_selection:

    """
    Selects qubits and their connectivity from a quantum chip based on specified constraints.

    Parameters:
        chip (chip): An instance of the chip class, defining the chip layout.
        qubit_index_max (int): Maximum allowable qubit index (default: 50).
        qubit_number (int): Number of qubits to select (default: 9).
        option (dict, optional): Selection options, including:
            - "max_qubits_per_row" (int): Maximum number of qubits per row.
            - "min_qubit_index" (int): Minimum allowable qubit index.
            - "max_qubit_index" (int): Maximum allowable qubit index.

    Methods:
        quselected():
            Returns selected qubit indices and their connectivity as a dictionary.
            Visualizes the selected qubits and connections on the chip grid.

    Features:
        - Adapts qubit selection based on chip layout and constraints.
        - Ensures logical connectivity for selected qubits.
    """

    def __init__(self, chip, qubit_index_max=50, qubit_number=9, option=None):
        self.chip = chip
        self.qubit_index_max = qubit_index_max
        self.qubit_number = int(qubit_number)  # Ensure this is an integer
        self.option = option if option is not None else {}
        self.rows = getattr(chip, 'rows', 12)      # Default to 12 rows if not specified
        self.columns = getattr(chip, 'columns', 13)  # Default to 13 columns if not specified


    def quselected(self):
        """
        Selects qubits and their connectivity based on the specified constraints.

        Returns:
            dict: 
                - "qubit_index_list" (list): Indices of selected qubits.
                - "qubit_connectivity" (list): Connectivity data as pairs of qubits.
        """
        # Retrieve constraints from options
        max_qubits_per_row = self.option.get('max_qubits_per_row', self.columns)  # Default to all qubits in a row
        min_qubit_index = self.option.get('min_qubit_index', 0)
        max_qubit_index = self.option.get('max_qubit_index', self.qubit_index_max)

        # Ensure qubit_number does not exceed the total qubits in the grid
        total_qubits = self.rows * self.columns
        qubit_number = min(self.qubit_number, total_qubits)

        best_selection = {
            "qubit_index_list": [],
            "qubit_connectivity": []
        }

        # Select qubits row by row, left to right
        qubit_indices = []
        for r in range(self.rows):
            for c in range(self.columns):
                q = r * self.columns + c
                if q >= min_qubit_index and q <= max_qubit_index:
                    qubit_indices.append(q)
                    if len(qubit_indices) == qubit_number:
                        break
            if len(qubit_indices) == qubit_number:
                break

        best_selection["qubit_index_list"] = qubit_indices

        # Create connectivity for horizontal and vertical connections
        qubit_connectivity = []

        # Horizontal connectivity (left-right)
        for r in range(self.rows):
            for c in range(self.columns - 1):  # Only connect to the right
                q1 = r * self.columns + c
                q2 = r * self.columns + (c + 1)
                if q1 in qubit_indices and q2 in qubit_indices:
                    qubit_connectivity.append([q1, q2])

        # Vertical connectivity (up-down)
        for r in range(self.rows - 1):  # Only connect down
            for c in range(self.columns):
                q1 = r * self.columns + c
                q2 = (r + 1) * self.columns + c
                if q1 in qubit_indices and q2 in qubit_indices:
                    qubit_connectivity.append([q1, q2])

        best_selection["qubit_connectivity"] = qubit_connectivity

        # If no selection was found, return empty lists
        if not best_selection["qubit_index_list"]:
            return best_selection

        # Print chip structure
        print(f"Chip Structure: {self.rows} rows x {self.columns} columns")
        print("Selected Qubits and Connectivity:")

        # Create a grid to visualize selected qubits and connectivity
        grid = [["." for _ in range(self.columns)] for _ in range(self.rows)]

        for q in best_selection["qubit_index_list"]:
            row = q // self.columns
            col = q % self.columns
            grid[row][col] = "Q"

        for conn in best_selection["qubit_connectivity"]:
            q1, q2 = conn
            r1, c1 = q1 // self.columns, q1 % self.columns
            r2, c2 = q2 // self.columns, q2 % self.columns
            if r1 == r2:  # Horizontal connection
                grid[r1][c1] = "-"
            elif c1 == c2:  # Vertical connection
                grid[r1][c1] = "|"

        for row in grid:
            print(" ".join(row))

        return best_selection


# Example usage:
# chip_instance = chip(rows=12, columns=13)
# qubit_selector = qubit_selection(chip_instance, qubit_number=10)
# qubit_selector.quselected()
