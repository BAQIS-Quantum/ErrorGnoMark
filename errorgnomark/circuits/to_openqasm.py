# errorgnomark/circuits/to_openqasm.py

"""
This module provides functions for converting the framework's internal QuantumCircuit
objects into other standard formats, such as OpenQASM.
"""

from typing import List

# Import the data structures this converter operates on.
# Using a relative import '.' assumes this file is in the 'circuits' package.
from .circuit import QuantumCircuit, Gate

def to_openqasm(
    circuit: 'QuantumCircuit', 
    measure_all: bool = True, 
    qasm_version: float = 2.0
) -> str:
    """
    Converts a framework-agnostic QuantumCircuit object to an OpenQASM string.
    
    This function supports converting 'delay' operations, with behavior dependent
    on the target QASM version.

    Args:
        circuit (QuantumCircuit): The circuit object to convert.
        measure_all (bool): If True, adds instructions to measure all qubits into
                            a classical register of the same size at the end.
                            This is crucial for execution on real hardware.
        qasm_version (float): The target OpenQASM version (e.g., 2.0 or 3.0).
                              This affects syntax and how 'delay' is handled.

    Returns:
        str: A string containing the full OpenQASM representation of the circuit.
        
    Raises:
        ValueError: If a gate in the circuit has no defined conversion rule,
                    or if an unsupported qasm_version is provided.
    """
    if not circuit.qubits:
        return f"OPENQASM {qasm_version:.1f};"

    if qasm_version not in [2.0, 3.0]:
        raise ValueError(f"Unsupported OpenQASM version: {qasm_version}. Must be 2.0 or 3.0.")

    num_qubits = max(circuit.qubits) + 1
    qasm_lines = []

    # 1. Header
    qasm_lines.append(f"OPENQASM {qasm_version:.1f};")
    if qasm_version < 3.0:
        qasm_lines.append('include "qelib1.inc";')
    qasm_lines.append("")

    # 2. Registers
    if qasm_version < 3.0:
        qasm_lines.append(f"qreg q[{num_qubits}];")
        if measure_all:
            qasm_lines.append(f"creg c[{num_qubits}];")
    else:  # OpenQASM 3.0 syntax
        qasm_lines.append(f"qubit[{num_qubits}] q;")
        if measure_all:
            qasm_lines.append(f"bit[{num_qubits}] c;")
    qasm_lines.append("")

    # 3. Gates and Instructions
    for gate in circuit.gates:
        gate_name = gate.name.lower()
        q_indices = gate.qubits
        params = gate.params

        # --- Handle 'delay' instruction (special case) ---
        if gate_name == 'delay':
            if qasm_version >= 3.0:
                if len(params) != 2 or not isinstance(params[0], (int, float)) or not isinstance(params[1], str):
                    raise ValueError("Delay gate expects params=[duration, unit], e.g., [100, 'ns'].")
                duration, unit = params
                qasm_lines.append(f"delay[{duration}{unit}] q[{q_indices[0]}];")
            else:
                # OQ2 Workaround: Use a barrier. This prevents optimizations across
                # this point but is NOT a timed delay. It's the closest equivalent.
                qubit_str = ", ".join([f"q[{i}]" for i in q_indices])
                qasm_lines.append(f"barrier {qubit_str}; // NOTE: Interpreted from a 'delay' operation.")
            continue  # Move to the next gate

        # --- Standard Gate to QASM Mapping ---
        line = ""
        # Parameterized gates
        if gate_name in ['rx', 'ry', 'rz', 'u1', 'p']:
            line = f"{gate_name}({params[0]}) q[{q_indices[0]}];"
        elif gate_name in ['u2']:
            line = f"{gate_name}({params[0]},{params[1]}) q[{q_indices[0]}];"
        elif gate_name in ['u3', 'u']:
            line = f"{gate_name}({params[0]},{params[1]},{params[2]}) q[{q_indices[0]}];"
        # Non-parameterized single-qubit gates
        elif gate_name in ['h', 'x', 'y', 'z', 's', 'sdg', 't', 'tdg', 'id']:
            line = f"{gate_name} q[{q_indices[0]}];"
        # Two-qubit gates
        elif gate_name == 'cnot':
            line = f"cx q[{q_indices[0]}],q[{q_indices[1]}];"
        elif gate_name == 'cz':
            line = f"cz q[{q_indices[0]}],q[{q_indices[1]}];"
        elif gate_name == 'swap':
            line = f"swap q[{q_indices[0]}],q[{q_indices[1]}];"
        elif gate_name == 'iswap':
            # iswap is not in qelib1.inc. Backend must support it or have a definition.
            line = f"iswap q[{q_indices[0]}],q[{q_indices[1]}];"
        
        if line:
            qasm_lines.append(line)
        else:
            # If a gate is not recognized, raise a clear error.
            raise ValueError(f"Gate '{gate.name}' has no defined conversion to OpenQASM.")

    # 4. Measurements
    if measure_all:
        qasm_lines.append("")
        qasm_lines.append("// Final Measurements")
        if qasm_version < 3.0:
            for q_idx in circuit.qubits:
                qasm_lines.append(f"measure q[{q_idx}] -> c[{q_idx}];")
        else:  # OpenQASM 3.0 measurement syntax
            qasm_lines.append("c = measure q;")
            
    return "\n".join(qasm_lines)