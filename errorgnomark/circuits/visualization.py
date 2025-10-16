# File Path: errorgnomark/circuits/visualization.py
# [FINAL VERSION WITH CZ/CNOT DISTINCTION & HIGHLIGHTING]

from typing import List, Dict, Tuple, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .circuit import QuantumCircuit, Gate

# --- Drawing Constants ---
GATE_BOX_WIDTH = 7
WIRE = '─' * GATE_BOX_WIDTH
CONNECTION = '│'.center(GATE_BOX_WIDTH)
CONTROL = '●'.center(GATE_BOX_WIDTH, '─')
TARGET_X = '⊕'.center(GATE_BOX_WIDTH, '─')
SWAP_X = '╳'.center(GATE_BOX_WIDTH, '─')
MEASURE = ' M '.center(GATE_BOX_WIDTH, '─')

def _get_gate_label(gate: "Gate", is_highlighted: bool = False) -> str:
    """Creates a label for a gate, with an option for a highlighted style."""
    name = gate.name.upper()
    if gate.params:
        param_str = ",".join([f"{p:.2f}" for p in gate.params])
        label = f"{name}({param_str})"
    else:
        label = name
    
    max_len = GATE_BOX_WIDTH - 2
    if len(label) > max_len:
        label = label[:max_len-1] + '…'
        
    if is_highlighted:
        return f"║{label:^{max_len}}║"
    else:
        return f"┤{label:^{max_len}}├"

def draw_circuit_text(circuit: "QuantumCircuit", highlighted_gates: Optional[List["Gate"]] = None) -> str:
    """
    Generates a professional, column-aligned text drawing of a quantum circuit.
    """
    if not circuit.gates:
        return str(circuit)

    highlighted_set: Set[int] = set(id(g) for g in highlighted_gates) if highlighted_gates else set()

    sorted_qubits = circuit.qubits
    qubit_to_row: Dict[int, int] = {q: i for i, q in enumerate(sorted_qubits)}
    num_qubits = len(sorted_qubits)

    col_ends = [0] * num_qubits
    gate_cols: List[int] = []
    for gate in circuit.gates:
        involved_rows = [qubit_to_row[q] for q in gate.qubits]
        start_col = 0
        if involved_rows:
            start_col = max(col_ends[r] for r in involved_rows)
        gate_cols.append(start_col)
        for r in involved_rows:
            col_ends[r] = start_col + 1
    num_cols = max(col_ends) if col_ends else 0
    
    grid: List[List[str]] = [[WIRE] * num_cols for _ in range(num_qubits)]

    for gate, col in zip(circuit.gates, gate_cols):
        is_highlighted = id(gate) in highlighted_set
        
        q_indices = gate.qubits
        rows = [qubit_to_row[q] for q in q_indices]
        min_row, max_row = min(rows), max(rows)

        if gate.is_measurement:
            grid[rows[0]][col] = MEASURE
            continue

        if len(rows) == 1:
            grid[rows[0]][col] = _get_gate_label(gate, is_highlighted)
            continue
            
        for r in range(min_row, max_row + 1):
            if grid[r][col] == WIRE:
                grid[r][col] = CONNECTION

        if gate.name.lower() == 'swap':
            grid[rows[0]][col] = SWAP_X
            grid[rows[1]][col] = SWAP_X
            continue

        control_rows = rows[:-1]
        target_row = rows[-1]

        for r in control_rows:
            grid[r][col] = CONTROL
        
        lower_name = gate.name.lower()
        
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        # [[[ BUG FIX: Correctly distinguish between CNOT and CZ gates ]]]
        if lower_name in ('cnot', 'cx'):
            # For CNOT, the target is '⊕'
            grid[target_row][col] = TARGET_X
        elif lower_name == 'cz':
            # For CZ, the target is also a control symbol '●'
            grid[target_row][col] = CONTROL
        else: # For other controlled gates like CRX, etc.
            target_gate_name = gate.name[1:] if len(gate.name) > 1 and gate.name.startswith('C') else gate.name
            temp_target_gate = type(gate)(name=target_gate_name, qubits=(gate.qubits[-1],), params=gate.params)
            grid[target_row][col] = _get_gate_label(temp_target_gate, is_highlighted)
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    output_lines = []
    for i, q in enumerate(sorted_qubits):
        label = f"q{q}: ".ljust(8)
        wire_line = "".join(grid[i])
        output_lines.append(label + wire_line)

    return "\n".join(output_lines)