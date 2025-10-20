# File Path: errorgnomark/simulators/statevector_simulator.py
# [DEFINITIVE MASTER VERSION - Architecturally Sound and Fully Functional]

import numpy as np
from typing import List, Dict

try:
    from errorgnomark.circuits.circuit import QuantumCircuit, Gate
    from errorgnomark.circuits.circuit import get_matrix as get_gate_matrix_from_map
    from errorgnomark.circuits.circuit import get_parameterized_matrix as get_parameterized_gate_matrix
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from errorgnomark.circuits.circuit import QuantumCircuit, Gate
    from errorgnomark.circuits.circuit import get_matrix as get_gate_matrix_from_map
    from errorgnomark.circuits.circuit import get_parameterized_matrix as get_parameterized_gate_matrix

class StatevectorSimulator:
    """
    A pure statevector simulator for ideal quantum circuit execution.

    This simulator is designed with a robust and scalable architecture. It does
    not hardcode gate matrices, but instead dynamically retrieves them from the
    central definitions in `circuit.py`. It uses a general permutation-based
    method to apply multi-qubit gates, allowing it to correctly simulate any
    gate on any set of qubits without special-case logic.
    """
    def __init__(self):
        self._qubit_map: Dict[int, int] = {}

    def _get_gate_matrix(self, gate: Gate) -> np.ndarray:
        """
        Retrieves the unitary matrix for a given gate.

        This method handles standard, parameterized, and special 'matrix_gate' types
        by delegating to the central gate definitions.
        """
        # Special handling for 'matrix_gate', where the matrix is the parameter.
        if gate.name.lower() == 'matrix_gate':
            if not gate.params or not isinstance(gate.params[0], np.ndarray):
                raise ValueError("Gate 'matrix_gate' requires a numpy array in its params.")
            return gate.params[0]
            
        try:
            # Dynamically get the matrix from the central source of truth (circuit.py)
            if gate.params:
                return get_parameterized_gate_matrix(gate)
            else:
                return get_gate_matrix_from_map(gate.name)
        except ValueError:
            raise NotImplementedError(f"Gate '{gate.name}' is not supported by the statevector simulator.")

    def _get_permutation_matrix(self, permutation: List[int], num_qubits: int) -> np.ndarray:
        """
        Generates the permutation matrix to reorder qubits for tensor products.
        This is the key to applying a gate to arbitrary qubit indices.
        """
        dim = 2**num_qubits
        basis_indices = np.arange(dim)
        
        # Convert indices to binary representation
        binary_basis = (((basis_indices[:, None] & (1 << np.arange(num_qubits - 1, -1, -1))) > 0)).astype(int)
        
        # Permute the columns (qubits) of the binary basis
        permuted_binary_basis = binary_basis[:, permutation]
        
        # Convert permuted binary back to indices
        permuted_indices = (permuted_binary_basis * (1 << np.arange(num_qubits - 1, -1, -1))).sum(axis=1)
        
        P = np.zeros((dim, dim), dtype=int)
        P[permuted_indices, basis_indices] = 1
        return P

    def _construct_operator(self, gate: Gate, num_qubits: int) -> np.ndarray:
        """
        Constructs the full N-qubit operator for a given gate using a general method.
        
        The method is U_full = P_inv @ (U_gate kron I) @ P, which correctly places
        the gate's action on the target qubits within the full Hilbert space.
        """
        gate_matrix = self._get_gate_matrix(gate)
        num_gate_qubits = len(gate.qubits)
        
        # Map the abstract qubit labels to their positions (0, 1, 2, ...)
        target_pos = [self._qubit_map[q] for q in gate.qubits]
        other_pos = [i for i in range(num_qubits) if i not in target_pos]
        
        # The permutation brings the target qubits to the 'front' (indices 0, 1, ...)
        permutation = target_pos + other_pos
        P = self._get_permutation_matrix(permutation, num_qubits)
        
        # The core operator acts on the first `num_gate_qubits` of the permuted space
        identity_part = np.eye(2**(num_qubits - num_gate_qubits))
        full_op = np.kron(gate_matrix, identity_part)
        
        # Permute the operator back to the original qubit ordering
        # For a unitary permutation matrix, P.T is the inverse.
        final_operator = P.T @ full_op @ P
        
        return final_operator

    def run(self, circuit: QuantumCircuit) -> np.ndarray:
        """
        Simulates the circuit and returns the final statevector.
        """
        num_qubits = len(circuit.qubits)
        self._qubit_map = {qubit: i for i, qubit in enumerate(circuit.qubits)}
        
        # Initial state |0...0>
        state_vector = np.zeros(2**num_qubits, dtype=complex)
        state_vector[0] = 1.0
        
        for gate in circuit.gates:
            # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
            # [[[ THE FINAL FIX: Ignore measurement gates ]]]
            # A statevector simulation calculates the state *before* measurement.
            # Measurement is a non-unitary operation and has no matrix, so we skip it.
            if gate.is_measurement:
                continue
            # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            
            # Construct the full operator for the current gate and apply it
            op_matrix = self._construct_operator(gate, num_qubits)
            state_vector = op_matrix @ state_vector
            
        return state_vector
