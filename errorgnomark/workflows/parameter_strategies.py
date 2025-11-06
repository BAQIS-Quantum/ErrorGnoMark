# errorgnomark/workflows/parameter_strategies.py

"""
Parameter generation strategies for experimental workflows.

This module provides classes for generating sequences of parameters to be
used in workflows. This allows for systematic sweeping over qubits, circuit
parameters, or other experimental variables.
"""

# -------------------------------------------------------------------
# 1. Standard Library Imports
# -------------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Tuple

# ==============================================================================
# Base Class for Parameter Strategies
# ==============================================================================

class BaseParameterStrategy(ABC):
    """Abstract base class for a parameter generation strategy."""

    @abstractmethod
    def generate(self, num_qubits: int, topology: List[Tuple[int, int]], **kwargs: Any) -> Iterator[Dict[str, Any]]:
        """
        Generates a sequence of parameter dictionaries for an experiment.

        Each yielded dictionary contains the parameters for a single run
        within a larger workflow.

        Args:
            num_qubits: The total number of qubits available on the device.
            topology: The connectivity graph of the device's qubits.
            **kwargs: Additional context for parameter generation.

        Yields:
            A dictionary of parameters for one experimental run.
        """
        pass

# ==============================================================================
# Concrete Strategy Implementations
# ==============================================================================

class SingleQubitSweep(BaseParameterStrategy):
    """
    A strategy that generates parameters for running an experiment on each
    qubit individually.
    """
    def generate(self, num_qubits: int, topology: List[Tuple[int, int]], **kwargs: Any) -> Iterator[Dict[str, Any]]:
        """
        Yields parameters to target each qubit from 0 to num_qubits-1.

        Example:
            For a 3-qubit device, this will yield:
            1. {'qubits': [0]}
            2. {'qubits': [1]}
            3. {'qubits': [2]}
        """
        for i in range(num_qubits):
            # The key 'qubits' is chosen to match the argument name in the API functions.
            yield {'qubits': [i]}

# --- Future Extension Example (Not fully implemented, for illustration) ---
class AllConnectedPairsSweep(BaseParameterStrategy):
    """
    A strategy that generates parameters for running a two-qubit experiment
    on every connected pair in the device topology.
    """
    def generate(self, num_qubits: int, topology: List[Tuple[int, int]], **kwargs: Any) -> Iterator[Dict[str, Any]]:
        """
        Yields parameters to target each pair in the topology.

        Example:
            For topology [(0, 1), (1, 2)], this will yield:
            1. {'qubits': [0, 1]}
            2. {'qubits': [1, 2]}
        """
        if not topology:
            # If no topology, yield nothing.
            return
        
        for pair in topology:
            yield {'qubits': list(pair)}