# # File Path: errorgnomark/experiments/gate_sets.py
# # FINAL, ALGORITHMICALLY CORRECTED VERSION: Fixes the critical bug in
# # UniversalXEBGateSet to ensure truly random circuits are generated.

# import abc
# import random
# from typing import Dict, List, Tuple, Union

# import numpy as np
# from scipy.linalg import expm

# from errorgnomark.circuits.circuit import Gate

# # --- Pauli Matrices (Helper) ---
# _X = np.array([[0, 1], [1, 0]], dtype=complex)
# _Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
# _Z = np.array([[1, 0], [0, -1]], dtype=complex)

# # ==============================================================================
# # --- Base Classes (Unchanged) ---
# # ==============================================================================
# class BaseGateSet(abc.ABC):
#     @abc.abstractmethod
#     def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
#         pass

# class SingleQubitGateSet(BaseGateSet):
#     pass

# class TwoQubitGateSet(BaseGateSet):
#     @abc.abstractmethod
#     def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
#         pass

# # ==============================================================================
# # --- Gate Set Implementations ---
# # ==============================================================================

# class CliffordGateSet(SingleQubitGateSet, TwoQubitGateSet):
#     """ A Clifford gate set compatible with both historical use and new MRB experiments. """
#     def __init__(self):
#         self.single_qubit_gates = [('H', (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]])), ('S', np.array([[1, 0], [0, 1j]]))]
#         self.two_qubit_gate_name = 'CNOT'
#         self.pauli_gates = [('X', _X), ('Y', _Y), ('Z', _Z)]
#         self._rb_1q_cliffords = [('H', 'H'), ('S', 'Sdg'), ('X', 'X'), ('Y', 'Y'), ('Z', 'Z')]
#         self._inverse_map = {'H': 'H', 'S': 'Sdg', 'X': 'X', 'Y': 'Y', 'Z': 'Z', 'CNOT': 'CNOT'}
#     def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
#         gates = []
#         for q in qubits:
#             name, _ = random.choice(self.single_qubit_gates)
#             gates.append(Gate(name=name, qubits=(q,)))
#         return gates
#     def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
#         return [Gate(name=self.two_qubit_gate_name, qubits=pair) for pair in topology]
#     def get_random_pauli_layer(self, qubits: List[int]) -> List[Gate]:
#         gates = []
#         for q in qubits:
#             name, _ = random.choice(self.pauli_gates)
#             gates.append(Gate(name=name, qubits=(q,)))
#         return gates
#     def get_random_clifford_and_inverse(self, qubits: List[int]) -> Tuple[List[Gate], List[Gate]]:
#         num_qubits = len(qubits)
#         if num_qubits == 1:
#             q = qubits[0]
#             fwd_name, inv_name = random.choice(self._rb_1q_cliffords)
#             return [Gate(name=fwd_name, qubits=(q,))], [Gate(name=inv_name, qubits=(q,))]
#         elif num_qubits == 2:
#             fwd_1q_sublayer, inv_1q_sublayer_rev = [], []
#             for q in qubits:
#                 fwd_name, inv_name = random.choice(self._rb_1q_cliffords)
#                 fwd_1q_sublayer.append(Gate(name=fwd_name, qubits=(q,)))
#                 inv_1q_sublayer_rev.insert(0, Gate(name=inv_name, qubits=(q,)))
#             fwd_cnot = Gate(name=self.two_qubit_gate_name, qubits=tuple(qubits))
#             inv_cnot = Gate(name=self._inverse_map[self.two_qubit_gate_name], qubits=tuple(qubits))
#             return fwd_1q_sublayer + [fwd_cnot], [inv_cnot] + inv_1q_sublayer_rev
#         else:
#             raise ValueError("This RB method is only for 1 or 2 qubits.")

# class XYGateSet(SingleQubitGateSet, TwoQubitGateSet):
#     def __init__(self):
#         self.single_qubit_gate_names = ['sqrtX', 'sqrtY']
#         self.two_qubit_gate_name = 'ISWAP'
#     def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
#         return [Gate(name=random.choice(self.single_qubit_gate_names), qubits=(q,)) for q in qubits]
#     def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
#         return [Gate(name=self.two_qubit_gate_name, qubits=pair) for pair in topology]

# class UniversalXEBGateSet(SingleQubitGateSet, TwoQubitGateSet):
#     """ A universal gate set for XEB that uses the "matrix_gate" contract. """
#     def __init__(self):
#         self.two_qubit_gate_name = 'CZ'
#         self._1q_matrices = self._precompute_1q_matrices()
#     def _precompute_1q_matrices(self) -> List[np.ndarray]:
#         matrices = []
#         xy_angles = np.linspace(0, 7/4 * np.pi, 8)
#         z_angles = np.linspace(0, 7/8 * np.pi, 8)
#         for theta in xy_angles:
#             axis_vector = np.cos(theta) * _X + np.sin(theta) * _Y
#             xy_rot_matrix = expm(-1j * (np.pi / 4) * axis_vector)
#             for alpha in z_angles:
#                 z_rot_matrix = expm(-1j * (alpha / 2) * _Z)
#                 full_matrix = z_rot_matrix @ xy_rot_matrix
#                 matrices.append(full_matrix)
#         return matrices
    
#     # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#     # [[[ THE CORRECTED METHOD ]]]
#     # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#     def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
#         gates = []
#         for q in qubits:
#             # For each qubit, choose a NEW, INDEPENDENT random matrix.
#             matrix = random.choice(self._1q_matrices)
#             gates.append(Gate(name="matrix_gate", qubits=(q,), params=[matrix]))
#         return gates
#     # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#     def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
#         return [Gate(name=self.two_qubit_gate_name, qubits=pair) for pair in topology]

# # ==============================================================================
# # --- Factory Function (Unchanged from last version) ---
# # ==============================================================================
# def get_gate_set(spec: Union[str, Dict, BaseGateSet]) -> BaseGateSet:
#     if isinstance(spec, BaseGateSet):
#         return spec
#     if isinstance(spec, str):
#         name = spec.lower()
#         if name == "clifford":
#             return CliffordGateSet()
#         elif name == "xy":
#             return XYGateSet()
#         elif name == "universal_xeb":
#             return UniversalXEBGateSet()
#         else:
#             raise ValueError(f"Unknown gate set name: '{spec}'. Available: ['clifford', 'xy', 'universal_xeb']")
#     if isinstance(spec, dict):
#         raise NotImplementedError("Custom gate sets via dictionary are not yet supported.")
#     raise TypeError(f"Invalid gate set specification type: {type(spec)}")

# File Path: errorgnomark/experiments/gate_sets.py
# MODIFIED: Added support for 3-qubit gate layers, enabling more complex RB/XEB.

import abc
import random
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.linalg import expm

from errorgnomark.circuits.circuit import Gate

# --- Pauli Matrices (Helper) ---
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)

# ==============================================================================
# --- Base Classes (Now with ThreeQubitGateSet) ---
# ==============================================================================
class BaseGateSet(abc.ABC):
    @abc.abstractmethod
    def get_random_1q_layer(self, qubits: List[int], seed: Optional[int] = None) -> List[Gate]:
        pass

class SingleQubitGateSet(BaseGateSet):
    pass

class TwoQubitGateSet(BaseGateSet):
    @abc.abstractmethod
    def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
        pass

# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# [[[ NEW ThreeQubitGateSet ABSTRACT CLASS ]]]
# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
class ThreeQubitGateSet(BaseGateSet):
    @abc.abstractmethod
    def get_random_3q_layer(self, topology: List[Tuple[int, int, int]], seed: Optional[int] = None) -> List[Gate]:
        """Generates a layer of random three-qubit gates for a given topology."""
        pass
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ==============================================================================
# --- Gate Set Implementations ---
# ==============================================================================

# CliffordGateSet now inherits from all three types
class CliffordGateSet(SingleQubitGateSet, TwoQubitGateSet, ThreeQubitGateSet):
    """
    A Clifford gate set supporting 1, 2, and 3-qubit operations.
    """
    def __init__(self, generation_method: str = 'from_generators'):
        if generation_method not in ['from_generators', 'uniform_from_c24_decompositions']:
            raise ValueError("generation_method must be 'from_generators' or 'uniform_from_c24_decompositions'")
        self.generation_method = generation_method

        # --- Gate Definitions ---
        self.single_qubit_generators = [('h',), ('s',), ('x',), ('y',), ('z',)]
        self.pauli_gates = [('x',), ('y',), ('z',)]
        self.two_qubit_gate_name = 'cnot'
        
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        # [[[ ADDED 3-QUBIT CLIFFORD GATES ]]]
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        self.three_qubit_clifford_gates = [('ccnot',), ('cswap',)] # Toffoli and Fredkin
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        # For RB: provide pairs with consistent (lowercase) names
        self._simple_clifford_inverse_pairs = [('h', 'h'), ('s', 'sdg'), ('x', 'x'), ('y', 'y'), ('z', 'z')]

        # Inverse map expanded for compatibility and new gates
        self._inverse_map = {
            'h': 'h', 'H': 'H',
            's': 'sdg', 'S': 'sdg',
            'sdg': 's', 'Sdg': 's',
            'x': 'x', 'X': 'X',
            'y': 'y', 'Y': 'Y',
            'z': 'z', 'Z': 'Z',
            'cnot': 'cnot', 'CNOT': 'cnot',
            # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
            'ccnot': 'ccnot', 'CCNOT': 'ccnot', 'toffoli': 'toffoli',
            'cswap': 'cswap', 'CSWAP': 'cswap', 'fredkin': 'fredkin',
            # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        }

        self._CLIFFORD_24_DECOMPOSITIONS = [
            ['id'], ['x'], ['y'], ['y', 'x'], ['rx90'], ['rxm90'], ['ry90'], ['rym90'],
            ['rxm90', 'ry90', 'rx90'], ['rxm90', 'rym90', 'rx90'], ['x', 'rym90'], ['x', 'ry90'],
            ['y', 'rx90'], ['y', 'rxm90'], ['rx90', 'ry90', 'rx90'], ['rxm90', 'rym90', 'rxm90'],
            ['ry90', 'rx90'], ['ry90', 'rxm90'], ['rym90', 'rx90'], ['rym90', 'rxm90'],
            ['rxm90', 'rym90'], ['rx90', 'rym90'], ['rxm90', 'ry90'], ['rx90', 'ry90'],
        ]

    def get_random_1q_layer(self, qubits: List[int], seed: Optional[int] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        if self.generation_method == 'from_generators':
            for q in qubits:
                name, = rng.choice(self.single_qubit_generators)
                gates.append(Gate(name=name, qubits=(q,)))
        elif self.generation_method == 'uniform_from_c24_decompositions':
            for q in qubits:
                gate_names = rng.choice(self._CLIFFORD_24_DECOMPOSITIONS)
                for name in gate_names:
                    gates.append(Gate(name=name, qubits=(q,)))
        return gates

    def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
        return [Gate(name=self.two_qubit_gate_name, qubits=pair) for pair in topology]

    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    # [[[ IMPLEMENTATION OF get_random_3q_layer ]]]
    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    def get_random_3q_layer(self, topology: List[Tuple[int, int, int]], seed: Optional[int] = None) -> List[Gate]:
        """Generates a layer of random three-qubit Clifford gates (e.g., CCNOT, CSWAP)."""
        rng = random.Random(seed)
        gates = []
        for triplet in topology:
            name, = rng.choice(self.three_qubit_clifford_gates)
            gates.append(Gate(name=name, qubits=triplet))
        return gates
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    def get_random_pauli_layer(self, qubits: List[int], seed: Optional[int] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        for q in qubits:
            name, = rng.choice(self.pauli_gates)
            gates.append(Gate(name=name, qubits=(q,)))
        return gates

    def get_random_clifford_and_inverse(self, qubits: List[int], seed: Optional[int] = None) -> Tuple[List[Gate], List[Gate]]:
        rng = random.Random(seed)
        num_qubits = len(qubits)
        if num_qubits == 1:
            q = qubits[0]
            if self.generation_method == 'from_generators':
                fwd_name, inv_name = rng.choice(self._simple_clifford_inverse_pairs)
                return [Gate(name=fwd_name, qubits=(q,))], [Gate(name=inv_name, qubits=(q,))]
            elif self.generation_method == 'uniform_from_c24_decompositions':
                fwd_gate_names = rng.choice(self._CLIFFORD_24_DECOMPOSITIONS)
                fwd_gates = [Gate(name=name, qubits=(q,)) for name in fwd_gate_names]
                inv_gates = [g.inverse() for g in reversed(fwd_gates)]
                return fwd_gates, inv_gates
        elif num_qubits == 2:
            fwd_1q_sublayer, inv_1q_sublayer_rev = [], []
            for q in qubits:
                fwd_name, inv_name = rng.choice(self._simple_clifford_inverse_pairs)
                fwd_1q_sublayer.append(Gate(name=fwd_name, qubits=(q,)))
                inv_1q_sublayer_rev.insert(0, Gate(name=inv_name, qubits=(q,)))
            fwd_cnot = Gate(name=self.two_qubit_gate_name, qubits=tuple(qubits))
            inv_cnot = fwd_cnot.inverse()
            return fwd_1q_sublayer + [fwd_cnot], [inv_cnot] + inv_1q_sublayer_rev
        else:
            # Note: RB for 3+ qubits is more complex and not implemented here.
            # This method is specific to 1 and 2 qubit RB.
            raise ValueError("This RB method is only for 1 or 2 qubits.")

# --- Other classes and factory function remain unchanged ---
class XYGateSet(SingleQubitGateSet, TwoQubitGateSet):
    def __init__(self):
        self.single_qubit_gate_names = ['sqrtX', 'sqrtY']
        self.two_qubit_gate_name = 'ISWAP'
    def get_random_1q_layer(self, qubits: List[int], seed: Optional[int] = None) -> List[Gate]:
        rng = random.Random(seed)
        return [Gate(name=rng.choice(self.single_qubit_gate_names), qubits=(q,)) for q in qubits]
    def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
        return [Gate(name=self.two_qubit_gate_name, qubits=pair) for pair in topology]

class UniversalXEBGateSet(SingleQubitGateSet, TwoQubitGateSet):
    def __init__(self):
        self.two_qubit_gate_name = 'CZ'
        self._1q_matrices = self._precompute_1q_matrices()
    def _precompute_1q_matrices(self) -> List[np.ndarray]:
        matrices = []
        xy_angles = np.linspace(0, 7/4 * np.pi, 8)
        z_angles = np.linspace(0, 7/8 * np.pi, 8)
        for theta in xy_angles:
            axis_vector = np.cos(theta) * _X + np.sin(theta) * _Y
            xy_rot_matrix = expm(-1j * (np.pi / 4) * axis_vector)
            for alpha in z_angles:
                z_rot_matrix = expm(-1j * (alpha / 2) * _Z)
                full_matrix = z_rot_matrix @ xy_rot_matrix
                matrices.append(full_matrix)
        return matrices
    def get_random_1q_layer(self, qubits: List[int], seed: Optional[int] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        for q in qubits:
            matrix = rng.choice(self._1q_matrices)
            gates.append(Gate(name="matrix_gate", qubits=(q,), params=[matrix]))
        return gates
    def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
        return [Gate(name=self.two_qubit_gate_name, qubits=pair) for pair in topology]

def get_gate_set(spec: Union[str, Dict, BaseGateSet]) -> BaseGateSet:
    if isinstance(spec, BaseGateSet):
        return spec
    if isinstance(spec, str):
        name = spec.lower()
        if name == "clifford":
            return CliffordGateSet()
        elif name == "xy":
            return XYGateSet()
        elif name == "universal_xeb":
            return UniversalXEBGateSet()
        else:
            raise ValueError(f"Unknown gate set name: '{spec}'. Available: ['clifford', 'xy', 'universal_xeb']")
    if isinstance(spec, dict):
        raise NotImplementedError("Custom gate sets via dictionary are not yet supported.")
    raise TypeError(f"Invalid gate set specification type: {type(spec)}")