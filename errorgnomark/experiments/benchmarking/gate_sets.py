# errorgnomark/experiments/benchmarking/gate_sets.py

import abc
import random
import math
from typing import Tuple

from errorgnomark.circuits.circuit import Gate

class SingleQubitGateSet(abc.ABC):
    """
    Abstract Base Class for a single-qubit gate set.

    This class defines the interface required for a valid gate set to be used
    in experiments like XEB. To create a custom gate set, you must inherit
    from this class and implement the `get_random_gate` method.
    """
    @abc.abstractmethod
    def get_random_gate(self, qubit: int) -> Gate:
        """
        Returns a single random gate from the set acting on the specified qubit.

        Args:
            qubit (int): The target qubit for the gate.

        Returns:
            Gate: A randomly chosen Gate object.
        """
        pass

# --- Pre-defined Gate Set Implementations ---

class CliffordGateSet(SingleQubitGateSet):
    """
    A gate set consisting of single-qubit Clifford gates.
    Specifically, this set includes Hadamard and Phase (S) gates, which can
    generate the entire single-qubit Clifford group.
    """
    def __init__(self):
        self._gates = [
            Gate(name='h', qubits=(0,)),  # Placeholder qubit, will be replaced
            Gate(name='s', qubits=(0,))
        ]

    def get_random_gate(self, qubit: int) -> Gate:
        """Returns a random H or S gate."""
        gate_template = random.choice(self._gates)
        return Gate(name=gate_template.name, qubits=(qubit,), params=gate_template.params)

class XYGateSet(SingleQubitGateSet):
    """
    A gate set of random rotations around the X and Y axes of the Bloch sphere.
    This is often called the "XY-plane" gate set.
    """
    def get_random_gate(self, qubit: int) -> Gate:
        """Returns a random Rx or Ry gate with a random angle."""
        angle = random.uniform(0, 2 * math.pi)
        gate_name = random.choice(['rx', 'ry'])
        return Gate(name=gate_name, qubits=(qubit,), params=[angle])