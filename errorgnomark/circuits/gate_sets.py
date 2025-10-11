# File Path: errorgnomark/circuits/gate_sets.py
# [CORRECTED & ENHANCED VERSION BASED ON YOUR NEW FILE]

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
    # [FIX 1] Add 'seed' parameter to the abstract method to enforce the API contract.
    # The calling code in xeb.py requires this parameter for reproducibility.
    @abc.abstractmethod
    def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[int] = None) -> List[Gate]:
        pass

class ThreeQubitGateSet(BaseGateSet):
    @abc.abstractmethod
    def get_random_3q_layer(self, topology: List[Tuple[int, int, int]], seed: Optional[int] = None) -> List[Gate]:
        pass

# ==============================================================================
# --- Gate Set Implementations ---
# ==============================================================================

class CliffordGateSet(SingleQubitGateSet, TwoQubitGateSet, ThreeQubitGateSet):
    def __init__(self, generation_method: str = 'from_generators'):
        if generation_method not in ['from_generators', 'uniform_from_c24_decompositions']:
            raise ValueError("generation_method must be 'from_generators' or 'uniform_from_c24_decompositions'")
        self.generation_method = generation_method
        self.single_qubit_generators = [('h',), ('s',), ('x',), ('y',), ('z',)]
        self.pauli_gates = [('x',), ('y',), ('z',)]
        self.two_qubit_gate_name = 'cnot'
        self.three_qubit_clifford_gates = [('ccnot',), ('cswap',)]
        self._simple_clifford_inverse_pairs = [('h', 'h'), ('s', 'sdg'), ('x', 'x'), ('y', 'y'), ('z', 'z')]
        self._inverse_map = {
            'h': 'h', 'H': 'H', 's': 'sdg', 'S': 'sdg', 'sdg': 's', 'Sdg': 's',
            'x': 'x', 'X': 'X', 'y': 'y', 'Y': 'Y', 'z': 'z', 'Z': 'Z',
            'cnot': 'cnot', 'CNOT': 'cnot', 'ccnot': 'ccnot', 'CCNOT': 'ccnot',
            'toffoli': 'toffoli', 'cswap': 'cswap', 'CSWAP': 'cswap', 'fredkin': 'fredkin',
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

    # [FIX 2] Implement the random, non-overlapping layer logic for 2-qubit gates.
    def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[int] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        available_pairs = topology[:]
        used_qubits = set()
        while available_pairs:
            pair_index = rng.randrange(len(available_pairs))
            q1, q2 = available_pairs.pop(pair_index)
            if q1 not in used_qubits and q2 not in used_qubits:
                gates.append(Gate(name=self.two_qubit_gate_name, qubits=(q1, q2)))
                used_qubits.add(q1)
                used_qubits.add(q2)
                available_pairs = [
                    (p_q1, p_q2) for p_q1, p_q2 in available_pairs
                    if p_q1 not in used_qubits and p_q2 not in used_qubits
                ]
        return gates

    def get_random_3q_layer(self, topology: List[Tuple[int, int, int]], seed: Optional[int] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        for triplet in topology:
            name, = rng.choice(self.three_qubit_clifford_gates)
            gates.append(Gate(name=name, qubits=triplet))
        return gates

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
            raise ValueError("This RB method is only for 1 or 2 qubits.")

class XYGateSet(SingleQubitGateSet, TwoQubitGateSet):
    def __init__(self):
        self.single_qubit_gate_names = ['sqrtX', 'sqrtY']
        self.two_qubit_gate_name = 'ISWAP'
    def get_random_1q_layer(self, qubits: List[int], seed: Optional[int] = None) -> List[Gate]:
        rng = random.Random(seed)
        return [Gate(name=rng.choice(self.single_qubit_gate_names), qubits=(q,)) for q in qubits]
    
    # [FIX 3] Apply the same fix to XYGateSet for consistency.
    def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[int] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        available_pairs = topology[:]
        used_qubits = set()
        while available_pairs:
            pair_index = rng.randrange(len(available_pairs))
            q1, q2 = available_pairs.pop(pair_index)
            if q1 not in used_qubits and q2 not in used_qubits:
                gates.append(Gate(name=self.two_qubit_gate_name, qubits=(q1, q2)))
                used_qubits.add(q1)
                used_qubits.add(q2)
                available_pairs = [
                    (p_q1, p_q2) for p_q1, p_q2 in available_pairs
                    if p_q1 not in used_qubits and p_q2 not in used_qubits
                ]
        return gates

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
    
    # [FIX 4] Apply the same fix to UniversalXEBGateSet for consistency.
    def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[int] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        available_pairs = topology[:]
        used_qubits = set()
        while available_pairs:
            pair_index = rng.randrange(len(available_pairs))
            q1, q2 = available_pairs.pop(pair_index)
            if q1 not in used_qubits and q2 not in used_qubits:
                gates.append(Gate(name=self.two_qubit_gate_name, qubits=(q1, q2)))
                used_qubits.add(q1)
                used_qubits.add(q2)
                available_pairs = [
                    (p_q1, p_q2) for p_q1, p_q2 in available_pairs
                    if p_q1 not in used_qubits and p_q2 not in used_qubits
                ]
        return gates

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