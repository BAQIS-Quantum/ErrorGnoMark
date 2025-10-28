# # File Path: errorgnomark/circuits/gate_sets.py
# # [FINAL INTEGRATED VERSION]
# # This version incorporates the user's scientific enhancements for CliffordGateSet
# # and resolves the conflict with UniversalXEBGateSet to align with the refactored
# # xeb.py, ensuring framework-wide consistency.

# import abc
# import random
# from typing import Dict, List, Optional, Tuple, Union

# import numpy as np

# from errorgnomark.circuits.circuit import Gate

# # ==============================================================================
# # --- Base Classes ---
# # ==============================================================================
# class BaseGateSet(abc.ABC):
#     @abc.abstractmethod
#     def get_random_1q_layer(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> List[Gate]:
#         pass

# class SingleQubitGateSet(BaseGateSet):
#     pass

# class TwoQubitGateSet(BaseGateSet):
#     @abc.abstractmethod
#     def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
#         pass

# class ThreeQubitGateSet(BaseGateSet):
#     @abc.abstractmethod
#     def get_random_3q_layer(self, topology: List[Tuple[int, int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
#         pass

# # ==============================================================================
# # --- Gate Set Implementations ---
# # ==============================================================================

# class CliffordGateSet(SingleQubitGateSet, TwoQubitGateSet, ThreeQubitGateSet):
#     """
#     Generates layers of Clifford gates for experiments like Randomized Benchmarking.
#     Includes scientifically robust sampling methods for 1 and 2 qubit Cliffords.
#     """
#     def __init__(self, generation_method: str = 'uniform_from_c24_decompositions'):
#         # [[[ USER ENHANCEMENT PRESERVED ]]] Default is the scientifically preferred method.
#         if generation_method not in ['from_generators', 'uniform_from_c24_decompositions']:
#             raise ValueError("generation_method must be 'from_generators' or 'uniform_from_c24_decompositions'")
#         self.generation_method = generation_method
        
#         # Kept for the 'from_generators' method
#         self._simple_clifford_inverse_pairs = [('h', 'h'), ('s', 'sdg'), ('x', 'x'), ('y', 'y'), ('z', 'z')]
        
#         self.pauli_gates = [('x',), ('y',), ('z',)]
#         self.two_qubit_gate_name = 'cnot'
#         self.three_qubit_clifford_gates = [('ccnot',), ('cswap',)]
        
#         # Decompositions for uniform sampling of the 24 single-qubit Cliffords.
#         # These are sequences of gates that generate each of the 24 elements.
#         self._CLIFFORD_24_DECOMPOSITIONS = [
#             ['id'], ['x'], ['y'], ['y', 'x'], ['s', 'h', 's'], ['sdg', 'h', 'sdg'], 
#             ['h'], ['h', 'x', 'h', 'y'], ['s'], ['sdg'], ['x', 's'], ['x', 'sdg'],
#             ['y', 's'], ['y', 'sdg'], ['h', 's'], ['h', 'sdg'], ['s', 'h'], ['sdg', 'h'],
#             ['h', 's', 'h'], ['h', 'sdg', 'h'], ['s', 'h', 's', 'h'], ['sdg', 'h', 'sdg', 'h'],
#             ['x', 'h'], ['y', 'h']
#         ]

#     def _get_random_1q_clifford_and_inverse(self, qubit: int, rng: random.Random) -> Tuple[List[Gate], List[Gate]]:
#         """
#         Helper to get a single random 1Q Clifford and its inverse, using the chosen method.
#         """
#         if self.generation_method == 'uniform_from_c24_decompositions':
#             fwd_gate_names = rng.choice(self._CLIFFORD_24_DECOMPOSITIONS)
#             fwd_gates = [Gate(name=name, qubits=(qubit,)) for name in fwd_gate_names if name != 'id']
#             # The inverse of a sequence of gates is the reversed sequence of inverse gates.
#             inv_gates = [g.inverse() for g in reversed(fwd_gates)]
#             return fwd_gates, inv_gates
#         else: # Fallback to simpler, non-uniform 'from_generators' method
#             fwd_name, inv_name = rng.choice(self._simple_clifford_inverse_pairs)
#             return [Gate(name=fwd_name, qubits=(qubit,))], [Gate(name=inv_name, qubits=(qubit,))]

#     def get_random_clifford_and_inverse(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> Tuple[List[Gate], List[Gate]]:
#         """
#         Generates a random n-qubit Clifford operation and its inverse.
#         For n=1, samples uniformly from the 24 1Q Cliffords (by default).
#         For n=2, samples from a broad subset of 2Q Cliffords using a standard decomposition.
#         """
#         rng = random.Random(seed)
#         num_qubits = len(qubits)
        
#         if num_qubits == 1:
#             return self._get_random_1q_clifford_and_inverse(qubits[0], rng)
            
#         elif num_qubits == 2:
#             # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#             # [[[ USER'S CRITICAL FIX PRESERVED ]]]
#             # This C = (C1a ⊗ C1b) * C_entangle * (C2a ⊗ C2b) structure provides
#             # much better coverage of the 2-qubit Clifford group, which is essential
#             # for a valid RB experiment.
#             q1, q2 = qubits[0], qubits[1]
            
#             # First layer of random 1Q Cliffords
#             c1a_fwd, c1a_inv = self._get_random_1q_clifford_and_inverse(q1, rng)
#             c1b_fwd, c1b_inv = self._get_random_1q_clifford_and_inverse(q2, rng)
            
#             # Entangling gate
#             fwd_cnot = Gate(name=self.two_qubit_gate_name, qubits=tuple(qubits))
#             inv_cnot = fwd_cnot.inverse()
            
#             # Second layer of random 1Q Cliffords
#             c2a_fwd, c2a_inv = self._get_random_1q_clifford_and_inverse(q1, rng)
#             c2b_fwd, c2b_inv = self._get_random_1q_clifford_and_inverse(q2, rng)
            
#             # Assemble the forward sequence: C1 * CNOT * C2
#             fwd_gates = c1a_fwd + c1b_fwd + [fwd_cnot] + c2a_fwd + c2b_fwd
            
#             # Assemble the inverse sequence: C2_inv * CNOT_inv * C1_inv
#             inv_gates = c2b_inv + c2a_inv + [inv_cnot] + c1b_inv + c1a_inv
            
#             return fwd_gates, inv_gates
#             # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            
#         else:
#             raise ValueError("This RB method is only implemented for 1 or 2 qubits.")

#     def get_random_1q_layer(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> List[Gate]:
#         rng = random.Random(seed)
#         gates = []
#         for q in qubits:
#             fwd_gates, _ = self._get_random_1q_clifford_and_inverse(q, rng)
#             gates.extend(fwd_gates)
#         return gates

#     def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
#         rng = random.Random(seed)
#         gates = []
#         available_pairs = list(topology)
#         used_qubits = set()
#         while available_pairs:
#             pair_index = rng.randrange(len(available_pairs))
#             q1, q2 = available_pairs.pop(pair_index)
#             if q1 not in used_qubits and q2 not in used_qubits:
#                 gates.append(Gate(name=self.two_qubit_gate_name, qubits=(q1, q2)))
#                 used_qubits.update([q1, q2])
#                 # Filter out pairs that reuse any of the just-used qubits
#                 available_pairs = [
#                     (p_q1, p_q2) for p_q1, p_q2 in available_pairs
#                     if p_q1 not in used_qubits and p_q2 not in used_qubits
#                 ]
#         return gates

#     def get_random_3q_layer(self, topology: List[Tuple[int, int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
#         rng = random.Random(seed)
#         return [Gate(name=rng.choice(self.three_qubit_clifford_gates)[0], qubits=triplet) for triplet in topology]

#     def get_random_pauli_layer(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> List[Gate]:
#         rng = random.Random(seed)
#         return [Gate(name=rng.choice(self.pauli_gates)[0], qubits=(q,)) for q in qubits]

# # --- The rest of the file remains unchanged to preserve compatibility ---

# class XYGateSet(SingleQubitGateSet, TwoQubitGateSet):
#     def __init__(self):
#         self.single_qubit_gate_names = ['sqrtX', 'sqrtY']
#         self.two_qubit_gate_name = 'ISWAP'
#     def get_random_1q_layer(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> List[Gate]:
#         rng = random.Random(seed)
#         return [Gate(name=rng.choice(self.single_qubit_gate_names), qubits=(q,)) for q in qubits]
    
#     def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
#         rng = random.Random(seed)
#         gates = []
#         available_pairs = list(topology)
#         used_qubits = set()
#         while available_pairs:
#             pair_index = rng.randrange(len(available_pairs))
#             q1, q2 = available_pairs.pop(pair_index)
#             if q1 not in used_qubits and q2 not in used_qubits:
#                 gates.append(Gate(name=self.two_qubit_gate_name, qubits=(q1, q2)))
#                 used_qubits.update([q1, q2])
#                 available_pairs = [
#                     (p_q1, p_q2) for p_q1, p_q2 in available_pairs
#                     if p_q1 not in used_qubits and p_q2 not in used_qubits
#                 ]
#         return gates

# class UniversalXEBGateSet(SingleQubitGateSet, TwoQubitGateSet):
#     """
#     Generates layers of universal, random single-qubit gates and a fixed
#     two-qubit gate, suitable for Cross-Entropy Benchmarking (XEB).
    
#     This implementation generates random U3 gates, which are natively supported
#     and can be decomposed into any basis by the QuantumCircuit.decompose method.
#     This avoids the need for special handling of 'matrix_gate' types.
#     """
#     def __init__(self):
#         self.two_qubit_gate_name = 'CZ'

#     def get_random_1q_layer(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> List[Gate]:
#         """
#         Generates a layer of random single-qubit gates by creating a random U3 gate
#         for each qubit, providing uniform (Haar-random) coverage of SU(2).
#         """
#         rng = random.Random(seed)
#         gates = []
#         for q in qubits:
#             # Standard parameterization for a Haar-random U3 gate
#             theta = np.arccos(1 - 2 * rng.random()) # More uniform than rng.uniform(0, np.pi)
#             phi = rng.uniform(0, 2 * np.pi)
#             lam = rng.uniform(0, 2 * np.pi)
#             # The 'u3' gate is natively decomposable by QuantumCircuit
#             gates.append(Gate('u3', (q,), params=(theta, phi, lam)))
#         return gates
    
#     def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
#         """
#         Generates a layer of two-qubit CZ gates based on the provided topology.
#         """
#         rng = random.Random(seed)
#         gates = []
#         available_pairs = list(topology)
#         used_qubits = set()
#         while available_pairs:
#             pair_index = rng.randrange(len(available_pairs))
#             q1, q2 = available_pairs.pop(pair_index)
#             if q1 not in used_qubits and q2 not in used_qubits:
#                 gates.append(Gate(name=self.two_qubit_gate_name, qubits=(q1, q2)))
#                 used_qubits.update([q1, q2])
#                 available_pairs = [
#                     (p_q1, p_q2) for p_q1, p_q2 in available_pairs
#                     if p_q1 not in used_qubits and p_q2 not in used_qubits
#                 ]
#         return gates

# def get_gate_set(spec: Union[str, Dict, BaseGateSet]) -> BaseGateSet:
#     """Factory function to retrieve a gate set object from a specification."""
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
# File Path: errorgnomark/circuits/gate_sets.py
# [FIXED VERSION - Generalizes Clifford Generation for N > 2 Qubits]
# This version resolves the ValueError by implementing a constructive method
# for generating multi-qubit Clifford elements.

import abc
import random
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from errorgnomark.circuits.circuit import Gate

# ==============================================================================
# --- Base Classes ---
# ==============================================================================
class BaseGateSet(abc.ABC):
    @abc.abstractmethod
    def get_random_1q_layer(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> List[Gate]:
        pass

class SingleQubitGateSet(BaseGateSet):
    pass

class TwoQubitGateSet(BaseGateSet):
    @abc.abstractmethod
    def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
        pass

class ThreeQubitGateSet(BaseGateSet):
    @abc.abstractmethod
    def get_random_3q_layer(self, topology: List[Tuple[int, int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
        pass

# ==============================================================================
# --- Gate Set Implementations ---
# ==============================================================================

class CliffordGateSet(SingleQubitGateSet, TwoQubitGateSet, ThreeQubitGateSet):
    """
    Generates layers of Clifford gates for experiments like Randomized Benchmarking.
    Includes scientifically robust sampling methods for 1 and 2 qubit Cliffords,
    and a constructive method for N > 2 qubits.
    """
    def __init__(self, generation_method: str = 'uniform_from_c24_decompositions'):
        if generation_method not in ['from_generators', 'uniform_from_c24_decompositions']:
            raise ValueError("generation_method must be 'from_generators' or 'uniform_from_c24_decompositions'")
        self.generation_method = generation_method
        
        self._simple_clifford_inverse_pairs = [('h', 'h'), ('s', 'sdg'), ('x', 'x'), ('y', 'y'), ('z', 'z')]
        
        self.pauli_gates = [('x',), ('y',), ('z',)]
        self.two_qubit_gate_name = 'cnot'
        self.three_qubit_clifford_gates = [('ccnot',), ('cswap',)]
        
        self._CLIFFORD_24_DECOMPOSITIONS = [
            ['id'], ['x'], ['y'], ['y', 'x'], ['s', 'h', 's'], ['sdg', 'h', 'sdg'], 
            ['h'], ['h', 'x', 'h', 'y'], ['s'], ['sdg'], ['x', 's'], ['x', 'sdg'],
            ['y', 's'], ['y', 'sdg'], ['h', 's'], ['h', 'sdg'], ['s', 'h'], ['sdg', 'h'],
            ['h', 's', 'h'], ['h', 'sdg', 'h'], ['s', 'h', 's', 'h'], ['sdg', 'h', 'sdg', 'h'],
            ['x', 'h'], ['y', 'h']
        ]

    def _get_random_1q_clifford_and_inverse(self, qubit: int, rng: random.Random) -> Tuple[List[Gate], List[Gate]]:
        """
        Helper to get a single random 1Q Clifford and its inverse, using the chosen method.
        """
        if self.generation_method == 'uniform_from_c24_decompositions':
            fwd_gate_names = rng.choice(self._CLIFFORD_24_DECOMPOSITIONS)
            fwd_gates = [Gate(name=name, qubits=(qubit,)) for name in fwd_gate_names if name != 'id']
            inv_gates = [g.inverse() for g in reversed(fwd_gates)]
            return fwd_gates, inv_gates
        else:
            fwd_name, inv_name = rng.choice(self._simple_clifford_inverse_pairs)
            return [Gate(name=fwd_name, qubits=(qubit,))], [Gate(name=inv_name, qubits=(qubit,))]

    def get_random_clifford_and_inverse(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> Tuple[List[Gate], List[Gate]]:
        """
        Generates a random n-qubit Clifford operation and its inverse.
        - For n=1, samples uniformly from the 24 1Q Cliffords.
        - For n=2, samples from a broad subset of 2Q Cliffords.
        - For n>2, constructively generates a random Clifford element.
        """
        rng = random.Random(seed)
        num_qubits = len(qubits)
        
        if num_qubits == 1:
            return self._get_random_1q_clifford_and_inverse(qubits[0], rng)
            
        elif num_qubits == 2:
            q1, q2 = qubits[0], qubits[1]
            
            c1a_fwd, c1a_inv = self._get_random_1q_clifford_and_inverse(q1, rng)
            c1b_fwd, c1b_inv = self._get_random_1q_clifford_and_inverse(q2, rng)
            
            fwd_cnot = Gate(name=self.two_qubit_gate_name, qubits=tuple(qubits))
            inv_cnot = fwd_cnot.inverse()
            
            c2a_fwd, c2a_inv = self._get_random_1q_clifford_and_inverse(q1, rng)
            c2b_fwd, c2b_inv = self._get_random_1q_clifford_and_inverse(q2, rng)
            
            fwd_gates = c1a_fwd + c1b_fwd + [fwd_cnot] + c2a_fwd + c2b_fwd
            inv_gates = c2b_inv + c2a_inv + [inv_cnot] + c1b_inv + c1a_inv
            
            return fwd_gates, inv_gates
            
        # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
        # MODIFIED: Added logic for N > 2 qubits instead of raising an error.
        # This constructively builds a random N-qubit Clifford element.
        else:
            fwd_gates = []
            
            # Layer 1: Random 1Q Cliffords on all qubits
            c1_fwd_layer = []
            c1_inv_layer = []
            for q in qubits:
                c_fwd, c_inv = self._get_random_1q_clifford_and_inverse(q, rng)
                c1_fwd_layer.extend(c_fwd)
                c1_inv_layer.extend(c_inv)
            fwd_gates.extend(c1_fwd_layer)

            # Layer 2: Entangling layer (linear chain of CNOTs)
            entangle_fwd_layer = []
            for i in range(num_qubits - 1):
                entangle_fwd_layer.append(Gate(self.two_qubit_gate_name, qubits=(qubits[i], qubits[i+1])))
            fwd_gates.extend(entangle_fwd_layer)
            entangle_inv_layer = [g.inverse() for g in reversed(entangle_fwd_layer)]

            # Layer 3: Another layer of random 1Q Cliffords
            c2_fwd_layer = []
            c2_inv_layer = []
            for q in qubits:
                c_fwd, c_inv = self._get_random_1q_clifford_and_inverse(q, rng)
                c2_fwd_layer.extend(c_fwd)
                c2_inv_layer.extend(c_inv)
            fwd_gates.extend(c2_fwd_layer)

            # Assemble the full inverse sequence in reverse order: C2_inv * Entangle_inv * C1_inv
            inv_gates = c2_inv_layer + entangle_inv_layer + c1_inv_layer
            
            return fwd_gates, inv_gates
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    def get_random_1q_layer(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        for q in qubits:
            fwd_gates, _ = self._get_random_1q_clifford_and_inverse(q, rng)
            gates.extend(fwd_gates)
        return gates

    def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        available_pairs = list(topology)
        used_qubits = set()
        while available_pairs:
            pair_index = rng.randrange(len(available_pairs))
            q1, q2 = available_pairs.pop(pair_index)
            if q1 not in used_qubits and q2 not in used_qubits:
                gates.append(Gate(name=self.two_qubit_gate_name, qubits=(q1, q2)))
                used_qubits.update([q1, q2])
                available_pairs = [
                    (p_q1, p_q2) for p_q1, p_q2 in available_pairs
                    if p_q1 not in used_qubits and p_q2 not in used_qubits
                ]
        return gates

    def get_random_3q_layer(self, topology: List[Tuple[int, int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
        rng = random.Random(seed)
        return [Gate(name=rng.choice(self.three_qubit_clifford_gates)[0], qubits=triplet) for triplet in topology]

    def get_random_pauli_layer(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> List[Gate]:
        rng = random.Random(seed)
        return [Gate(name=rng.choice(self.pauli_gates)[0], qubits=(q,)) for q in qubits]

# --- The rest of the file remains unchanged ---

class XYGateSet(SingleQubitGateSet, TwoQubitGateSet):
    def __init__(self):
        self.single_qubit_gate_names = ['sqrtX', 'sqrtY']
        self.two_qubit_gate_name = 'ISWAP'
    def get_random_1q_layer(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> List[Gate]:
        rng = random.Random(seed)
        return [Gate(name=rng.choice(self.single_qubit_gate_names), qubits=(q,)) for q in qubits]
    
    def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        available_pairs = list(topology)
        used_qubits = set()
        while available_pairs:
            pair_index = rng.randrange(len(available_pairs))
            q1, q2 = available_pairs.pop(pair_index)
            if q1 not in used_qubits and q2 not in used_qubits:
                gates.append(Gate(name=self.two_qubit_gate_name, qubits=(q1, q2)))
                used_qubits.update([q1, q2])
                available_pairs = [
                    (p_q1, p_q2) for p_q1, p_q2 in available_pairs
                    if p_q1 not in used_qubits and p_q2 not in used_qubits
                ]
        return gates

class UniversalXEBGateSet(SingleQubitGateSet, TwoQubitGateSet):
    def __init__(self):
        self.two_qubit_gate_name = 'CZ'

    def get_random_1q_layer(self, qubits: List[int], seed: Optional[Union[int, float]] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        for q in qubits:
            theta = np.arccos(1 - 2 * rng.random())
            phi = rng.uniform(0, 2 * np.pi)
            lam = rng.uniform(0, 2 * np.pi)
            gates.append(Gate('u3', (q,), params=(theta, phi, lam)))
        return gates
    
    def get_random_2q_layer(self, topology: List[Tuple[int, int]], seed: Optional[Union[int, float]] = None) -> List[Gate]:
        rng = random.Random(seed)
        gates = []
        available_pairs = list(topology)
        used_qubits = set()
        while available_pairs:
            pair_index = rng.randrange(len(available_pairs))
            q1, q2 = available_pairs.pop(pair_index)
            if q1 not in used_qubits and q2 not in used_qubits:
                gates.append(Gate(name=self.two_qubit_gate_name, qubits=(q1, q2)))
                used_qubits.update([q1, q2])
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