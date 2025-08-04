# errorgnomark/experiments/gate_sets.py
import abc
import random
import math
from typing import Tuple

# This import will now work because we defined Gate in circuit.py
from ..circuits.circuit import Gate

class SingleQubitGateSet(abc.ABC):
    """
    Abstract Base Class for a single-qubit gate set.
    """
    @abc.abstractmethod
    def get_random_gate(self, qubit: int) -> Gate:
        """
        Returns a single random gate from the set acting on the specified qubit.
        """
        pass

class CliffordGateSet(SingleQubitGateSet):
    """
    A gate set consisting of single-qubit Clifford gates.
    """
    def __init__(self):
        # Template gates. The qubit index will be replaced.
        self._gates = [
            Gate(name='h', qubits=(0,)),
            Gate(name='s', qubits=(0,))
        ]

    def get_random_gate(self, qubit: int) -> Gate:
        """Returns a random H or S gate."""
        gate_template = random.choice(self._gates)
        # Create a new Gate instance with the correct target qubit
        return Gate(name=gate_template.name, qubits=(qubit,))

class XYGateSet(SingleQubitGateSet):
    """
    A gate set of random rotations around the X and Y axes.
    """
    def get_random_gate(self, qubit: int) -> Gate:
        """Returns a random Rx or Ry gate with a random angle."""
        angle = random.uniform(0, 2 * math.pi)
        gate_name = random.choice(['rx', 'ry'])
        return Gate(name=gate_name, qubits=(qubit,), params=[angle])