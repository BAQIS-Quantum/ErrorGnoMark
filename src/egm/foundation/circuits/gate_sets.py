# File Path: egm/core/circuits/gate_sets.py
# [FINAL UNIFIED VERSION for egm-src]
# Combines EGM’s multi-qubit Clifford generation with Sycamore & XEB sets.
# ==============================================================================
# Author: Integrated version by OpenAI (2026)
# ==============================================================================

import abc
import random
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from egm.foundation.circuits.circuit import Gate

# ==============================================================================
# --- Base Classes ---
# ==============================================================================

class BaseGateSet(abc.ABC):
    @abc.abstractmethod
    def get_random_1q_layer(
        self,
        qubits: List[int],
        seed: Optional[Union[int, float]] = None
    ) -> List[Gate]:
        """Return one layer of random single‑qubit gates."""
        pass


class SingleQubitGateSet(BaseGateSet):
    """Marker class for single‑qubit gate sets."""
    pass


class TwoQubitGateSet(BaseGateSet):
    @abc.abstractmethod
    def get_random_2q_layer(
        self,
        topology: List[Tuple[int, int]],
        seed: Optional[Union[int, float]] = None
    ) -> List[Gate]:
        pass


class ThreeQubitGateSet(BaseGateSet):
    @abc.abstractmethod
    def get_random_3q_layer(
        self,
        topology: List[Tuple[int, int, int]],
        seed: Optional[Union[int, float]] = None
    ) -> List[Gate]:
        pass

# ==============================================================================
# --- Gate Set Implementations ---
# ==============================================================================

class CliffordGateSet(SingleQubitGateSet, TwoQubitGateSet, ThreeQubitGateSet):
    """
    Generates layers of Clifford gates for experiments like Randomized Benchmarking.
    Includes robust sampling for 1Q/2Q and constructive n>2 generation.
    """

    def __init__(self, generation_method: str = 'uniform_from_c24_decompositions'):
        if generation_method not in ['from_generators', 'uniform_from_c24_decompositions']:
            raise ValueError("generation_method must be 'from_generators' or 'uniform_from_c24_decompositions'")
        self.generation_method = generation_method

        self._simple_clifford_inverse_pairs = [
            ('h', 'h'), ('s', 'sdg'), ('x', 'x'), ('y', 'y'), ('z', 'z')
        ]
        self.pauli_gates = [('x',), ('y',), ('z',)]
        self.two_qubit_gate_name = 'cnot'
        self.three_qubit_clifford_gates = [('ccnot',), ('cswap',)]

        self._CLIFFORD_24_DECOMPOSITIONS = [
            ['id'], ['x'], ['y'], ['y', 'x'], ['s', 'h', 's'], ['sdg', 'h', 'sdg'],
            ['h'], ['h', 'x', 'h', 'y'], ['s'], ['sdg'], ['x', 's'], ['x', 'sdg'],
            ['y', 's'], ['y', 'sdg'], ['h', 's'], ['h', 'sdg'], ['s', 'h'], ['sdg', 'h'],
            ['h', 's', 'h'], ['h', 'sdg', 'h'], ['s', 'h', 's', 'h'],
            ['sdg', 'h', 'sdg', 'h'], ['x', 'h'], ['y', 'h']
        ]

    def _get_random_1q_clifford_and_inverse(
        self, qubit: int, rng: random.Random
    ) -> Tuple[List[Gate], List[Gate]]:
        """Return random 1Q Clifford and its inverse."""
        if self.generation_method == 'uniform_from_c24_decompositions':
            seq = rng.choice(self._CLIFFORD_24_DECOMPOSITIONS)
            fwd = [Gate(name=g, qubits=(qubit,)) for g in seq if g != 'id']
            inv = [g.inverse() for g in reversed(fwd)]
            return fwd, inv
        else:
            fwd, inv = rng.choice(self._simple_clifford_inverse_pairs)
            return [Gate(fwd, (qubit,))], [Gate(inv, (qubit,))]

    def get_random_clifford_and_inverse(
        self, qubits: List[int], seed: Optional[Union[int, float]] = None
    ) -> Tuple[List[Gate], List[Gate]]:
        """Generate random Clifford (any # of qubits)."""
        rng = random.Random(seed)
        n = len(qubits)
        if n == 1:
            return self._get_random_1q_clifford_and_inverse(qubits[0], rng)
        elif n == 2:
            q1, q2 = qubits
            c1a_f, c1a_i = self._get_random_1q_clifford_and_inverse(q1, rng)
            c1b_f, c1b_i = self._get_random_1q_clifford_and_inverse(q2, rng)
            cnot = Gate(self.two_qubit_gate_name, (q1, q2))
            cnot_inv = cnot.inverse()
            c2a_f, c2a_i = self._get_random_1q_clifford_and_inverse(q1, rng)
            c2b_f, c2b_i = self._get_random_1q_clifford_and_inverse(q2, rng)
            fwd = c1a_f + c1b_f + [cnot] + c2a_f + c2b_f
            inv = c2b_i + c2a_i + [cnot_inv] + c1b_i + c1a_i
            return fwd, inv
        else:
            fwd, inv = [], []
            c1_f, c1_i = [], []
            for q in qubits:
                f, i = self._get_random_1q_clifford_and_inverse(q, rng)
                c1_f.extend(f)
                c1_i.extend(i)
            fwd.extend(c1_f)
            ent_fwd = [Gate(self.two_qubit_gate_name, (qubits[i], qubits[i + 1])) for i in range(n - 1)]
            fwd.extend(ent_fwd)
            ent_inv = [g.inverse() for g in reversed(ent_fwd)]
            c2_f, c2_i = [], []
            for q in qubits:
                f, i = self._get_random_1q_clifford_and_inverse(q, rng)
                c2_f.extend(f)
                c2_i.extend(i)
            fwd.extend(c2_f)
            inv = c2_i + ent_inv + c1_i
            return fwd, inv

    def get_random_1q_layer(self, qubits, seed=None):
        rng = random.Random(seed)
        gates = []
        for q in qubits:
            fwd, _ = self._get_random_1q_clifford_and_inverse(q, rng)
            gates.extend(fwd)
        return gates

    def get_random_2q_layer(self, topology, seed=None):
        rng = random.Random(seed)
        pairs = list(topology)
        gates = []
        used = set()
        while pairs:
            q1, q2 = pairs.pop(rng.randrange(len(pairs)))
            if q1 not in used and q2 not in used:
                gates.append(Gate(self.two_qubit_gate_name, (q1, q2)))
                used |= {q1, q2}
                pairs = [(a, b) for a, b in pairs if a not in used and b not in used]
        return gates

    def get_random_3q_layer(self, topology, seed=None):
        rng = random.Random(seed)
        return [Gate(rng.choice(self.three_qubit_clifford_gates)[0], t) for t in topology]

    def get_random_pauli_layer(self, qubits, seed=None):
        rng = random.Random(seed)
        return [Gate(rng.choice(self.pauli_gates)[0], (q,)) for q in qubits]

# ==============================================================================

class XYGateSet(SingleQubitGateSet, TwoQubitGateSet):
    """Google-style iSWAP + SX/SY gate set."""
    def __init__(self):
        self.single_qubit_gate_names = ['sx', 'sy']
        self.two_qubit_gate_name = 'iswap'

    def get_random_1q_layer(self, qubits, seed=None):
        rng = random.Random(seed)
        return [Gate(rng.choice(self.single_qubit_gate_names), (q,)) for q in qubits]

    def get_random_2q_layer(self, topology, seed=None):
        rng = random.Random(seed)
        pairs = list(topology)
        gates = []
        used = set()
        while pairs:
            q1, q2 = pairs.pop(rng.randrange(len(pairs)))
            if q1 not in used and q2 not in used:
                gates.append(Gate(self.two_qubit_gate_name, (q1, q2)))
                used |= {q1, q2}
                pairs = [(a, b) for a, b in pairs if a not in used and b not in used]
        return gates

# ==============================================================================

class UniversalXEBGateSet(SingleQubitGateSet, TwoQubitGateSet):
    """Generates Haar-random U3 1Q gates and fixed CZ gates for XEB."""
    def __init__(self):
        self.two_qubit_gate_name = 'CZ'

    def get_random_1q_layer(self, qubits, seed=None):
        rng = random.Random(seed)
        gates = []
        for q in qubits:
            theta = np.arccos(1 - 2 * rng.random())
            phi = rng.uniform(0, 2 * np.pi)
            lam = rng.uniform(0, 2 * np.pi)
            gates.append(Gate('u3', (q,), params=(theta, phi, lam)))
        return gates

    def get_random_2q_layer(self, topology, seed=None):
        rng = random.Random(seed)
        pairs = list(topology)
        gates = []
        used = set()
        while pairs:
            q1, q2 = pairs.pop(rng.randrange(len(pairs)))
            if q1 not in used and q2 not in used:
                gates.append(Gate(self.two_qubit_gate_name, (q1, q2)))
                used |= {q1, q2}
                pairs = [(a, b) for a, b in pairs if a not in used and b not in used]
        return gates

# ==============================================================================

class SycamoreXEBGateSet(SingleQubitGateSet, TwoQubitGateSet):
    """Sycamore-style gate set for Google's XEB and quantum supremacy benchmarks."""
    def __init__(self, single_qubit_mode="64_grid", two_qubit_gate="iswap"):
        if single_qubit_mode not in ["64_grid", "xy_simple"]:
            raise ValueError("single_qubit_mode must be '64_grid' or 'xy_simple'")
        self.single_qubit_mode = single_qubit_mode
        self.two_qubit_gate_name = two_qubit_gate.lower()

        axes = np.linspace(0, 2 * np.pi, 8, endpoint=False)
        zph = np.linspace(0, 2 * np.pi, 8, endpoint=False)
        self._U3_table = [(np.pi / 2, phi, lam) for phi in axes for lam in zph]
        self._simple_single_qubit_gates = ['sx', 'sy', 'sw']

    def get_random_1q_layer(self, qubits, seed=None):
        rng = random.Random(seed)
        gates = []
        if self.single_qubit_mode == "64_grid":
            for q in qubits:
                gates.append(Gate("u3", (q,), params=rng.choice(self._U3_table)))
        else:
            for q in qubits:
                gates.append(Gate(rng.choice(self._simple_single_qubit_gates), (q,)))
        return gates

    def get_random_2q_layer(self, topology, seed=None):
        rng = random.Random(seed)
        pairs = list(topology)
        gates = []
        used = set()
        while pairs:
            q1, q2 = pairs.pop(rng.randrange(len(pairs)))
            if q1 not in used and q2 not in used:
                gates.append(Gate(self.two_qubit_gate_name, (q1, q2)))
                used |= {q1, q2}
                pairs = [(a, b) for a, b in pairs if a not in used and b not in used]
        return gates

# ==============================================================================

def get_gate_set(spec: Union[str, Dict, BaseGateSet]) -> BaseGateSet:
    """Return the appropriate GateSet instance."""
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
        elif name in ["sycamore_xeb", "sycamore", "google_sycamore"]:
            return SycamoreXEBGateSet()

        raise ValueError(
            f"Unknown gate set: {spec}. "
            "Available: ['clifford', 'xy', 'universal_xeb', 'sycamore_xeb']"
        )

    if isinstance(spec, dict):
        raise NotImplementedError("Custom gate set dict specs are not yet supported.")

    raise TypeError(f"Invalid gate set spec type: {type(spec)}")

# ==============================================================================
# END OF FILE
# ==============================================================================