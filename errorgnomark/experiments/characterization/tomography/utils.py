# File Path: errorgnomark/experiments/characterization/tomography/utils.py

from typing import List, Dict
from errorgnomark.circuits.circuit import QuantumCircuit, Gate
# 使用相对路径导入同级目录下的 basis 模块，非常清晰
from .basis import TOMOGRAPHY_BASIS_MAP

def get_measurement_circuits(qubits: List[int]) -> Dict[str, QuantumCircuit]:
    """
    Generates the measurement circuits for all bases defined in TOMOGRAPHY_BASIS_MAP.
    """
    measurement_circuits = {}
    num_qubits = len(qubits)

    for basis_name, basis_ops in TOMOGRAPHY_BASIS_MAP.items():
        gates = []
        for i in range(num_qubits):
            qubit_index = qubits[i]
            op_name = basis_name[i]

            if op_name == 'X':
                gates.append(Gate('h', (qubit_index,)))
            elif op_name == 'Y':
                # Apply S-dagger then H to rotate Y-basis to Z-basis
                gates.append(Gate('sdg', (qubit_index,)))
                gates.append(Gate('h', (qubit_index,)))
            # For 'Z' basis, no gates are needed.

        measurement_circuits[basis_name] = QuantumCircuit(qubits=qubits, gates=gates)
        
    return measurement_circuits