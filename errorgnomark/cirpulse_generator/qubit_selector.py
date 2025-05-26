import networkx as nx
from matplotlib import rcParams
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']  # matplotlib自带
plt.rcParams['axes.unicode_minus'] = False


def build_chessboard_graph(chip_row, chip_col, file_path=r"", run_all=False):
    """
    Build the chessboard (grid) quantum chip graph and filter available nodes.

    Functionality:
    1. Read quantum chip parameters and connectivity from a CSV file
    2. Construct a 2D grid graph (nodes indexed by row/col)
    3. Filter usable nodes based on nonzero T1/T2/Fidelity parameters
    4. Establish connectivity between nodes (for CZ gates)

    Parameters:
        chip_row (int): Number of chip rows
        chip_col (int): Number of chip columns
        file_path (str): CSV file path (parameter file)

    Returns:
        tuple: (networkx.Graph, list of available node IDs)
            - Graph object contains node positions and edges
            - Available node list contains IDs of nodes meeting parameter requirements

    CSV file column requirements:
        The file should contain these columns (in order):
        - Column 0: Node ID (e.g., '0', '1', ...)
        - Column 1: T1 time (μs)
        - Column 2: T2 time (μs)
        - Column 3: Single qubit gate fidelity (0-1)
        - Column 4: Frequency (GHz)
        - Column 5: Connectivity, e.g., '0_1:0.5' (CZ value between node 0 and 1)
    """

    # Set Chinese font for display (can be replaced as needed)
    # rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei']
    rcParams['axes.unicode_minus'] = False  # Fix negative sign display

    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: file not found {file_path}")
        return None, None
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None, None

    # Create grid graph
    G = nx.Graph()

    # Add all nodes (indexed by row and column)
    for row in range(1, chip_row + 1):
        for col in range(1, chip_col + 1):
            node_num = (row-1)*chip_col + (col-1)
            node_name = str(node_num)
            G.add_node(node_name, pos=(col, -row))  # negative y for plotting convention

    # Parse connectivity (column 6)
    connections = df.iloc[:, 5].dropna()

    for connection_str in connections:
        connection_list = connection_str.splitlines()
        for connection in connection_list:
            if '_' in connection and ':' in connection:
                nodes_part, cz_value = connection.split(':')
                nodes_part = nodes_part.strip()
                cz_value = cz_value.strip()
                if not run_all:
                    if cz_value != '0':
                        node1, node2 = nodes_part.split('_')
                        if node1 in G.nodes and node2 in G.nodes:
                            G.add_edge(node1, node2)
                        else:
                            print(f"Warning: connection {connection} contains non-existent node")
                else:
                    node1, node2 = nodes_part.split('_')
                    if node1 in G.nodes and node2 in G.nodes:
                        G.add_edge(node1, node2)

    if not run_all:
        # Filter available nodes (all T1/T2/Fidelity nonzero)
        available_nodes = []
        for index, row in df.iterrows():
            node_id = str(row.iloc[0])
            t1 = row.iloc[1]
            t2 = row.iloc[2]
            fidelity = row.iloc[3]
            if t1 != 0 and t2 != 0 and fidelity != 0:
                if node_id in G.nodes:
                    available_nodes.append(node_id)
                else:
                    print(f"Warning: node {node_id} has valid parameters but not in the graph")
    else:
        available_nodes = []
        for index, row in df.iterrows():
            node_id = str(row.iloc[0])
            if node_id in G.nodes:
                available_nodes.append(node_id)

    return G, available_nodes

def visualize_chessboard(G, available_nodes):
    """
    Visualize the grid quantum chip connectivity graph.

    Functionality:
    1. Show 2D layout of the chip
    2. Use different colors for available/unavailable nodes
    3. Show edges (connections)
    4. Show labels only for available nodes

    Parameters:
        G (networkx.Graph): Graph object from build_chessboard_graph
        available_nodes (list): List of available node IDs

    Display legend:
        - Available nodes: light blue
        - Unavailable nodes: black
        - Edges: gray
        - Labels: only available nodes
    """

    if G is None:
        print("Warning: input graph is None")
        return

    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei']
    plt.rcParams['axes.unicode_minus'] = False

    pos = nx.get_node_attributes(G, 'pos')
    available = [node for node in G.nodes if node in available_nodes]
    unavailable = [node for node in G.nodes if node not in available_nodes]

    plt.figure(figsize=(10, 8))
    nx.draw_networkx_nodes(G, pos, nodelist=available,
                           node_color='lightblue',
                           node_size=300,
                           edgecolors='black',
                           linewidths=0.5)
    nx.draw_networkx_nodes(G, pos, nodelist=unavailable,
                           node_color='black',
                           node_size=300,
                           alpha=0.7)
    nx.draw_networkx_edges(G, pos, edge_color='gray', width=1.5, alpha=0.5)
    labels = {node: node for node in available}
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_color='black')

    plt.title("Quantum chip connectivity\n(Blue: available nodes, Black: unavailable nodes)", pad=20)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def select_connected_nodes(chessboard_graph, available_nodes, X, df, initial_qubit,
                           weights=None):
    """
    Select a set of X connected nodes with the best quantum parameters.

    Functionality:
    1. Evaluate node quality using quantum parameters (T1/T2/Fidelity/Frequency)
    2. Prefer nodes with high degree and high parameter scores
    3. Ensure selected nodes form a connected subgraph
    4. Return selected nodes and their internal edge count

    Parameters:
        chessboard_graph (nx.Graph): Topology graph (with node positions)
        available_nodes (list): List of available node IDs (already parameter-filtered)
        X (int): Number of nodes to select
        df (pd.DataFrame): Quantum parameter DataFrame, must include:
            - Column 0: Node ID
            - Column 1: T1 time (μs)
            - Column 2: T2 time (μs)
            - Column 3: Single qubit fidelity (0-1)
            - Column 4: Frequency (GHz)
        initial_qubit: Initial node for selection
        weights (dict): Optional, weight for each parameter, e.g.,
                        {'T1':0.3, 'T2':0.2, 'Fidelity':0.4, 'Frequency':0.1}

    Returns:
        tuple: (selected_nodes, edge_count)
            - selected_nodes: List of selected node IDs
            - edge_count: Number of edges among these nodes

    Algorithm:
        1. Compute a weighted score for each node
        2. Find all connected components (fully connected subgraphs)
        3. For sufficiently large components:
           a. Compute node priority (degree + score)
           b. Start from the highest-priority node and expand selection
           c. Ensure each new node is directly connected to selected set
        4. If no component is large enough, return the largest subgraph
    """

    if weights is None:
        weights = {'T1': 0.25, 'T2': 0.25, 'Fidelity': 0.3, 'Frequency': 0.2}

    param_scores = {}
    for node in available_nodes:
        try:
            row = df[df.iloc[:, 0].astype(str) == str(node)].iloc[0]
            t1 = row.iloc[1] / df.iloc[:, 1].max()
            t2 = row.iloc[2] / df.iloc[:, 2].max()
            fidelity = row.iloc[3]
            freq = 1 - abs(row.iloc[4] - df.iloc[:, 4].median()) / df.iloc[:, 4].std()
            score = (t1 * weights['T1'] +
                     t2 * weights['T2'] +
                     fidelity * weights['Fidelity'] +
                     freq * weights['Frequency'])
            param_scores[node] = score
        except:
            param_scores[node] = 0

    available_graph = chessboard_graph.subgraph(available_nodes).copy()
    connected_components = sorted(nx.connected_components(available_graph),
                                  key=len, reverse=True)

    for component in connected_components:
        if len(component) >= X:
            subgraph = available_graph.subgraph(component)
            degrees = dict(subgraph.degree())
            max_degree = max(degrees.values())
            node_priority = {
                node: 0.8 * (degrees[node] / max_degree) +
                      0.2 * param_scores[node]
                for node in degrees
            }
            sorted_nodes = sorted(node_priority.keys(),
                                  key=lambda x: node_priority[x],
                                  reverse=True)
            selected = set([str(initial_qubit)])
            while len(selected) < X and len(selected) < len(sorted_nodes):
                candidates = set()
                for node in selected:
                    candidates.update(neighbor for neighbor in subgraph.neighbors(node)
                                      if neighbor not in selected)
                if not candidates:
                    break
                next_node = max(candidates, key=lambda x: node_priority[x])
                selected.add(next_node)
            if len(selected) == X:
                edge_count = subgraph.subgraph(selected).number_of_edges()
                return list(selected), edge_count

    largest_component = connected_components[0]
    edge_count = available_graph.subgraph(largest_component).number_of_edges()
    return list(largest_component), edge_count

def save_to_txt(node_indices, selected_connections, file_path='node_indices & selected_connections.txt'):
    """
    Save node indices and connection list to a text file.

    Functionality:
    1. Save quantum chip node information in a readable format
    2. Automatically handle different formats of connection lists (list or str)
    3. Add section headers for readability
    4. Robust error handling

    Parameters:
        node_indices (list): Node indices, e.g., [0, 1, 2] or ['0','1','2']
        selected_connections (list): Connection list; accepts:
            - String format: ['0_1', '1_2']
            - List format: [[0,1], [1,2]]
        file_path (str): Output file path (default: current directory)

    Example file format:
        === Nodes ===
        0
        1
        2

        === Connections ===
        0_1
        1_2
    """

    try:
        with open(file_path, 'w') as f:
            f.write("=== Nodes ===\n")
            f.write('\n'.join(map(str, node_indices)) + '\n\n')
            f.write("=== Connections ===\n")
            for conn in selected_connections:
                if isinstance(conn, list):
                    f.write(f"{'_'.join(map(str, conn))}\n")
                else:
                    f.write(f"{conn}\n")
        print(f"Nodes and connections saved to {file_path}")
    except PermissionError:
        print(f"Error: no write permission {file_path}")
    except Exception as e:
        print(f"Unexpected error saving file: {str(e)}")

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
    def __init__(self, rows=12, cols=13, qubit_index_max=50, qubit_to_be_used=9,
                 initial_qubit=0,
                 option=None, file_path='', weights=None, run_all=False):
        self.qubit_index_max = qubit_index_max
        self.qubit_to_be_used = int(qubit_to_be_used)
        self.option = option if option is not None else {}
        self.rows = rows
        self.columns = cols
        self.file_path = file_path
        self.weights = weights
        self.initial_qubit = initial_qubit
        self.run_all = run_all

    def quselected(self):
        """
        Selects qubits and their connectivity based on the specified constraints.

        Returns:
            dict: 
                - "qubit_index_list" (list): Indices of selected qubits.
                - "qubit_connectivity" (list): Connectivity data as pairs of qubits.
        """
        if not self.run_all:
            chessboard_graph, available_nodes = build_chessboard_graph(self.rows, self.columns, file_path=self.file_path,
                                                                       run_all=self.run_all)
            if 1:
                visualize_chessboard(chessboard_graph, available_nodes)
            if self.qubit_to_be_used > len(available_nodes):
                print(f"Requested qubit count {self.qubit_to_be_used} exceeds available: {len(available_nodes)}. Please select again.")
            df = pd.read_csv(self.file_path)
            selected_nodes, edge_count = select_connected_nodes(chessboard_graph, available_nodes, self.qubit_to_be_used,
                                                                df=df,
                                                                initial_qubit=self.initial_qubit,
                                                                weights=self.weights)
            if 1:
                pos = nx.get_node_attributes(chessboard_graph, 'pos')
                plt.figure(figsize=(10, 8))
                nx.draw_networkx_nodes(chessboard_graph, pos, node_color='lightgray', node_size=100)
                nx.draw_networkx_edges(chessboard_graph, pos, edge_color='lightgray')
                subgraph = chessboard_graph.subgraph(selected_nodes)
                nx.draw_networkx_nodes(subgraph, pos, node_color='red', node_size=300)
                nx.draw_networkx_edges(subgraph, pos, edge_color='red', width=2)
                labels = {node: node for node in selected_nodes}
                nx.draw_networkx_labels(chessboard_graph, pos, labels, font_size=8)
                plt.title(f"Selected {self.qubit_to_be_used} adjacent nodes (red)")
                plt.show()
            node_indices = sorted(int(x) for x in selected_nodes)
            selected_connections = []
            for edge in chessboard_graph.edges:
                node1, node2 = edge
                if node1 in selected_nodes and node2 in selected_nodes:
                    idx1 = int(node1)
                    idx2 = int(node2)
                    selected_connections.append([idx1, idx2])
            save_to_txt(node_indices, selected_connections)
            best_selection = {"qubit_index_list": node_indices, "qubit_connectivity": selected_connections}
        else:
            chessboard_graph, available_nodes = build_chessboard_graph(self.rows, self.columns, file_path=self.file_path,
                                                                       run_all=self.run_all)
            node_indices = sorted(int(x) for x in available_nodes)
            selected_connections = []
            for edge in chessboard_graph.edges:
                node1, node2 = edge
                if node1 in available_nodes and node2 in available_nodes:
                    idx1 = int(node1)
                    idx2 = int(node2)
                    selected_connections.append([idx1, idx2])
            save_to_txt(node_indices, selected_connections)
            best_selection = {"qubit_index_list": node_indices, "qubit_connectivity": selected_connections}
        return best_selection


