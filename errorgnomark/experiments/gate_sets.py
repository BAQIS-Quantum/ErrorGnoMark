
# # # errorgnomark/experiments/gate_sets.py

# # import abc
# # import random
# # from typing import Dict, List, Tuple, Union

# # import numpy as np

# # # This now correctly imports your Gate definition
# # from errorgnomark.circuits.circuit import Gate

# # class BaseGateSet(abc.ABC):
# #     @abc.abstractmethod
# #     def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
# #         pass

# # class SingleQubitGateSet(BaseGateSet):
# #     pass

# # class TwoQubitGateSet(BaseGateSet):
# #     @abc.abstractmethod
# #     def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
# #         pass

# # class CliffordGateSet(SingleQubitGateSet, TwoQubitGateSet):
# #     def __init__(self):
# #         # Your original single-qubit gates
# #         self.single_qubit_gates = [
# #             ('H', (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]])),
# #             ('S', np.array([[1, 0], [0, 1j]])),
# #         ]
# #         # Your original two-qubit gate
# #         self.two_qubit_gate_name = 'CNOT'

# #         # --- [ADDITION 1] ---
# #         # Define Pauli gates, required for MRB circuit construction.
# #         self.pauli_gates = [
# #             ('X', np.array([[0, 1], [1, 0]])),
# #             ('Y', np.array([[0, -1j], [1j, 0]])),
# #             ('Z', np.array([[1, 0], [0, -1]]))
# #         ]
# #         # --- [END ADDITION 1] ---

# #     def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
# #         gates = []
# #         for q in qubits:
# #             name, _ = random.choice(self.single_qubit_gates)
# #             gates.append(Gate(name=name, qubits=(q,)))
# #         return gates

# #     def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
# #         gates = []
# #         for pair in topology:
# #             gates.append(Gate(name=self.two_qubit_gate_name, qubits=pair))
# #         return gates

# #     # --- [ADDITION 2] ---
# #     # This method was missing and is required by mrb.py
# #     def get_random_pauli_layer(self, qubits: List[int]) -> List[Gate]:
# #         """Generates a layer of random single-qubit Pauli gates."""
# #         gates = []
# #         for q in qubits:
# #             name, _ = random.choice(self.pauli_gates)
# #             gates.append(Gate(name=name, qubits=(q,)))
# #         return gates
# #     # --- [END ADDITION 2] ---


# # class XYGateSet(SingleQubitGateSet, TwoQubitGateSet):
# #     def __init__(self):
# #         self.single_qubit_gate_names = ['sqrtX', 'sqrtY']
# #         self.two_qubit_gate_name = 'ISWAP'

# #     def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
# #         gates = []
# #         for q in qubits:
# #             name = random.choice(self.single_qubit_gate_names)
# #             gates.append(Gate(name=name, qubits=(q,)))
# #         return gates

# #     def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
# #         gates = []
# #         for pair in topology:
# #             gates.append(Gate(name=self.two_qubit_gate_name, qubits=pair))
# #         return gates


# # # --- [ADDITION 3] ---
# # # This factory function was missing and caused the ImportError.
# # def get_gate_set(spec: Union[str, Dict, BaseGateSet]) -> BaseGateSet:
# #     """
# #     Factory function to get a gate set instance from a specification.
# #     """
# #     if isinstance(spec, BaseGateSet):
# #         return spec
    
# #     if isinstance(spec, str):
# #         name = spec.lower()
# #         if name == "clifford":
# #             return CliffordGateSet()
# #         elif name == "xy":
# #             return XYGateSet()
# #         else:
# #             raise ValueError(f"Unknown gate set name: '{spec}'. Available: ['clifford', 'xy']")
            
# #     if isinstance(spec, dict):
# #         raise NotImplementedError("Custom gate sets via dictionary are not yet supported.")
        
# #     raise TypeError(f"Invalid gate set specification type: {type(spec)}")
# # # --- [END ADDITION 3] ---

# # File Path: errorgnomark/experiments/gate_sets.py
# # MODIFIED to be backward-compatible while adding new functionality for RB.

# import abc
# import random
# from typing import Dict, List, Tuple, Union

# import numpy as np

# from errorgnomark.circuits.circuit import Gate

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

# class CliffordGateSet(SingleQubitGateSet, TwoQubitGateSet):
#     def __init__(self):
#         # --- EXISTING ATTRIBUTES (UNCHANGED FOR COMPATIBILITY) ---
#         self.single_qubit_gates = [
#             ('H', (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]])),
#             ('S', np.array([[1, 0], [0, 1j]])),
#         ]
#         self.two_qubit_gate_name = 'CNOT'
#         self.pauli_gates = [
#             ('X', np.array([[0, 1], [1, 0]])),
#             ('Y', np.array([[0, -1j], [1j, 0]])),
#             ('Z', np.array([[1, 0], [0, -1]]))
#         ]
        
#         # --- [NEW ADDITION 1] ---
#         # A more complete set of 1Q Cliffords and their inverses, used by the new RB method.
#         # This does not affect the original `single_qubit_gates` list.
#         self._rb_1q_cliffords = [
#             # (Forward Gate Name, Inverse Gate Name)
#             ('H', 'H'),
#             ('S', 'Sdg'),
#             ('X', 'X'),
#             ('Y', 'Y'),
#             ('Z', 'Z'),
#         ]
#         # Map for all known inverses, used internally by the new method.
#         self._inverse_map = {
#             'H': 'H', 'S': 'Sdg', 'X': 'X', 'Y': 'Y', 'Z': 'Z',
#             'CNOT': 'CNOT'
#         }
#         # --- [END NEW ADDITION 1] ---

#     # --- EXISTING METHODS (UNCHANGED FOR COMPATIBILITY) ---
#     def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
#         gates = []
#         for q in qubits:
#             name, _ = random.choice(self.single_qubit_gates)
#             gates.append(Gate(name=name, qubits=(q,)))
#         return gates

#     def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
#         gates = []
#         for pair in topology:
#             gates.append(Gate(name=self.two_qubit_gate_name, qubits=pair))
#         return gates

#     def get_random_pauli_layer(self, qubits: List[int]) -> List[Gate]:
#         """Generates a layer of random single-qubit Pauli gates."""
#         gates = []
#         for q in qubits:
#             name, _ = random.choice(self.pauli_gates)
#             gates.append(Gate(name=name, qubits=(q,)))
#         return gates

#     # --- [NEW ADDITION 2] ---
#     # A new method specifically for generating RB sequences.
#     # It provides both the forward and inverse gates, which is required for RB.
#     def get_random_clifford_and_inverse(self, qubits: List[int]) -> Tuple[List[Gate], List[Gate]]:
#         """
#         Generates a random Clifford layer and its corresponding inverse layer.
#         This is the recommended method for building a valid RB sequence.

#         Returns:
#             A tuple: (forward_gates, inverse_gates)
#         """
#         num_qubits = len(qubits)
        
#         if num_qubits == 1:
#             q = qubits[0]
#             fwd_name, inv_name = random.choice(self._rb_1q_cliffords)
#             forward_gates = [Gate(name=fwd_name, qubits=(q,))]
#             inverse_gates = [Gate(name=inv_name, qubits=(q,))]
#             return forward_gates, inverse_gates

#         elif num_qubits == 2:
#             # A 2Q RB layer is random 1Q Cliffords + a CNOT.
#             # Its inverse is CNOT_inv + inverse 1Q Cliffords in reverse order.
            
#             fwd_1q_sublayer, inv_1q_sublayer_rev = [], []
#             for q in qubits:
#                 fwd_name, inv_name = random.choice(self._rb_1q_cliffords)
#                 fwd_1q_sublayer.append(Gate(name=fwd_name, qubits=(q,)))
#                 inv_1q_sublayer_rev.insert(0, Gate(name=inv_name, qubits=(q,)))

#             fwd_cnot = Gate(name=self.two_qubit_gate_name, qubits=tuple(qubits))
#             inv_cnot = Gate(name=self._inverse_map[self.two_qubit_gate_name], qubits=tuple(qubits))

#             forward_gates = fwd_1q_sublayer + [fwd_cnot]
#             inverse_gates = [inv_cnot] + inv_1q_sublayer_rev
            
#             return forward_gates, inverse_gates
        
#         else:
#             raise ValueError("This RB method is only for 1 or 2 qubits.")
#     # --- [END NEW ADDITION 2] ---


# class XYGateSet(SingleQubitGateSet, TwoQubitGateSet):
#     # ... (This class remains completely unchanged)
#     def __init__(self):
#         self.single_qubit_gate_names = ['sqrtX', 'sqrtY']
#         self.two_qubit_gate_name = 'ISWAP'
#     def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
#         gates = []
#         for q in qubits:
#             name = random.choice(self.single_qubit_gate_names)
#             gates.append(Gate(name=name, qubits=(q,)))
#         return gates
#     def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
#         gates = []
#         for pair in topology:
#             gates.append(Gate(name=self.two_qubit_gate_name, qubits=pair))
#         return gates


# # --- EXISTING FACTORY FUNCTION (UNCHANGED FOR COMPATIBILITY) ---
# def get_gate_set(spec: Union[str, Dict, BaseGateSet]) -> BaseGateSet:
#     if isinstance(spec, BaseGateSet):
#         return spec
#     if isinstance(spec, str):
#         name = spec.lower()
#         if name == "clifford":
#             return CliffordGateSet()
#         elif name == "xy":
#             return XYGateSet()
#         else:
#             raise ValueError(f"Unknown gate set name: '{spec}'. Available: ['clifford', 'xy']")
#     if isinstance(spec, dict):
#         raise NotImplementedError("Custom gate sets via dictionary are not yet supported.")
#     raise TypeError(f"Invalid gate set specification type: {type(spec)}")
# File Path: errorgnomark/experiments/gate_sets.py
# FINAL LIBRARY VERSION: This version integrates the UniversalXEBGateSet
# directly into the library, making it available via the factory function.
# It is fully backward-compatible with the historical versions provided.
# File Path: errorgnomark/experiments/gate_sets.py
# FINAL CORRECTED VERSION: Merges RB-compatible features with the new
# UniversalXEBGateSet, making it compatible with both demo_mrb.py and demo_xeb.py.

# File Path: errorgnomark/experiments/gate_sets.py
# FINAL, ALGORITHMICALLY CORRECTED VERSION: Fixes the critical bug in
# UniversalXEBGateSet to ensure truly random circuits are generated.

import abc
import random
from typing import Dict, List, Tuple, Union

import numpy as np
from scipy.linalg import expm

from errorgnomark.circuits.circuit import Gate

# --- Pauli Matrices (Helper) ---
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)

# ==============================================================================
# --- Base Classes (Unchanged) ---
# ==============================================================================
class BaseGateSet(abc.ABC):
    @abc.abstractmethod
    def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
        pass

class SingleQubitGateSet(BaseGateSet):
    pass

class TwoQubitGateSet(BaseGateSet):
    @abc.abstractmethod
    def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
        pass

# ==============================================================================
# --- Gate Set Implementations ---
# ==============================================================================

class CliffordGateSet(SingleQubitGateSet, TwoQubitGateSet):
    """ A Clifford gate set compatible with both historical use and new MRB experiments. """
    def __init__(self):
        self.single_qubit_gates = [('H', (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]])), ('S', np.array([[1, 0], [0, 1j]]))]
        self.two_qubit_gate_name = 'CNOT'
        self.pauli_gates = [('X', _X), ('Y', _Y), ('Z', _Z)]
        self._rb_1q_cliffords = [('H', 'H'), ('S', 'Sdg'), ('X', 'X'), ('Y', 'Y'), ('Z', 'Z')]
        self._inverse_map = {'H': 'H', 'S': 'Sdg', 'X': 'X', 'Y': 'Y', 'Z': 'Z', 'CNOT': 'CNOT'}
    def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
        gates = []
        for q in qubits:
            name, _ = random.choice(self.single_qubit_gates)
            gates.append(Gate(name=name, qubits=(q,)))
        return gates
    def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
        return [Gate(name=self.two_qubit_gate_name, qubits=pair) for pair in topology]
    def get_random_pauli_layer(self, qubits: List[int]) -> List[Gate]:
        gates = []
        for q in qubits:
            name, _ = random.choice(self.pauli_gates)
            gates.append(Gate(name=name, qubits=(q,)))
        return gates
    def get_random_clifford_and_inverse(self, qubits: List[int]) -> Tuple[List[Gate], List[Gate]]:
        num_qubits = len(qubits)
        if num_qubits == 1:
            q = qubits[0]
            fwd_name, inv_name = random.choice(self._rb_1q_cliffords)
            return [Gate(name=fwd_name, qubits=(q,))], [Gate(name=inv_name, qubits=(q,))]
        elif num_qubits == 2:
            fwd_1q_sublayer, inv_1q_sublayer_rev = [], []
            for q in qubits:
                fwd_name, inv_name = random.choice(self._rb_1q_cliffords)
                fwd_1q_sublayer.append(Gate(name=fwd_name, qubits=(q,)))
                inv_1q_sublayer_rev.insert(0, Gate(name=inv_name, qubits=(q,)))
            fwd_cnot = Gate(name=self.two_qubit_gate_name, qubits=tuple(qubits))
            inv_cnot = Gate(name=self._inverse_map[self.two_qubit_gate_name], qubits=tuple(qubits))
            return fwd_1q_sublayer + [fwd_cnot], [inv_cnot] + inv_1q_sublayer_rev
        else:
            raise ValueError("This RB method is only for 1 or 2 qubits.")

class XYGateSet(SingleQubitGateSet, TwoQubitGateSet):
    def __init__(self):
        self.single_qubit_gate_names = ['sqrtX', 'sqrtY']
        self.two_qubit_gate_name = 'ISWAP'
    def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
        return [Gate(name=random.choice(self.single_qubit_gate_names), qubits=(q,)) for q in qubits]
    def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
        return [Gate(name=self.two_qubit_gate_name, qubits=pair) for pair in topology]

class UniversalXEBGateSet(SingleQubitGateSet, TwoQubitGateSet):
    """ A universal gate set for XEB that uses the "matrix_gate" contract. """
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
    
    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    # [[[ THE CORRECTED METHOD ]]]
    # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    def get_random_1q_layer(self, qubits: List[int]) -> List[Gate]:
        gates = []
        for q in qubits:
            # For each qubit, choose a NEW, INDEPENDENT random matrix.
            matrix = random.choice(self._1q_matrices)
            gates.append(Gate(name="matrix_gate", qubits=(q,), params=[matrix]))
        return gates
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    def get_random_2q_layer(self, topology: List[Tuple[int, int]]) -> List[Gate]:
        return [Gate(name=self.two_qubit_gate_name, qubits=pair) for pair in topology]

# ==============================================================================
# --- Factory Function (Unchanged from last version) ---
# ==============================================================================
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