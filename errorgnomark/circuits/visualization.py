# errorgnomark/circuits/visualization.py

from typing import List, Dict, Set
from ..circuits.circuit import QuantumCircuit, Gate

def _group_gates_into_layers(gates: List[Gate]) -> List[List[Gate]]:
    """
    Groups a flat list of gates into layers of non-conflicting gates.

    A layer is a set of gates that can be executed concurrently because
    they operate on disjoint sets of qubits.

    Args:
        gates: A flat list of Gate objects.

    Returns:
        A list of layers, where each layer is a list of Gate objects.
    """
    layers: List[List[Gate]] = []
    for gate in gates:
        gate_qubits = set(gate.qubits)
        placed_in_existing_layer = False
        for layer in layers:
            # Check if the gate conflicts with any gate already in the layer
            qubits_in_layer: Set[int] = set()
            for existing_gate in layer:
                qubits_in_layer.update(existing_gate.qubits)
            
            if gate_qubits.isdisjoint(qubits_in_layer):
                # No conflict, place the gate in this layer
                layer.append(gate)
                placed_in_existing_layer = True
                break
        
        if not placed_in_existing_layer:
            # If the gate couldn't fit in any existing layer, create a new one
            layers.append([gate])
            
    return layers

def format_circuit_as_string(circuit: QuantumCircuit) -> str:
    """
    Generates a text-based string representation of a quantum circuit.

    This function arranges gates into layers and draws them on text-based
    wires for each qubit, providing a clear visualization for debugging.

    Args:
        circuit: The QuantumCircuit object to visualize.

    Returns:
        A multi-line string representing the circuit diagram.
    """
    if not circuit.qubits:
        return "(Empty Circuit)"

    sorted_qubits = sorted(circuit.qubits)
    qubit_label_width = max(len(f"q{q}") for q in sorted_qubits) + 2  # e.g., "q10: "

    # Initialize the output lines for each qubit wire
    lines: Dict[int, str] = {
        q: f"q{q}:".ljust(qubit_label_width) for q in sorted_qubits
    }
    
    # Group gates into layers for clean visualization
    layers = _group_gates_into_layers(circuit.gates)

    for layer in layers:
        gates_in_layer: Dict[int, Gate] = {}
        for gate in layer:
            for qubit in gate.qubits:
                gates_in_layer[qubit] = gate

        # Determine the maximum width needed for gate symbols in this layer
        max_symbol_width = 0
        if layer:
            max_symbol_width = max(len(g.name) + 2 for g in layer)
        max_symbol_width = max(max_symbol_width, 3) # Ensure at least '---' width

        for q in sorted_qubits:
            gate_symbol = ""
            if q in gates_in_layer:
                gate = gates_in_layer[q]
                if len(gate.qubits) == 1:
                    # Single-qubit gate
                    symbol = f"[{gate.name}]"
                    gate_symbol = symbol.center(max_symbol_width, '-')
                else:
                    # Two-qubit gate
                    # Assume the first qubit in the tuple is the control
                    if q == gate.qubits[0]: 
                        symbol = "●" # Control symbol
                    else:
                        symbol = f"[{gate.name}]" # Target symbol
                    gate_symbol = symbol.center(max_symbol_width, '-')
            else:
                # This qubit is idle in this layer
                gate_symbol = '-' * max_symbol_width
            
            lines[q] += gate_symbol + '-'

    return "\n".join(lines.values())