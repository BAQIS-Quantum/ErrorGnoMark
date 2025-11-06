# errorgnomark/workflows/base.py

"""
Base classes for the Workflow module.

This file defines the fundamental abstract base classes (ABCs) that govern the
structure of all workflows in ErrorGnoMark. The primary goal is to establish a
consistent interface for defining, executing, and managing complex experimental
sequences.
"""

# -------------------------------------------------------------------
# 1. Standard Library Imports
# -------------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import Any, Dict

# -------------------------------------------------------------------
# 2. Internal Framework Imports
# -------------------------------------------------------------------
from errorgnomark.engine.executor import QuantumEngine


# ==============================================================================
# Abstract Base Class for all Workflows
# ==============================================================================

class BaseWorkflow(ABC):
    """
    An abstract base class for an experimental workflow.

    A workflow represents a high-level experimental procedure that may involve
    running one or more underlying protocols, potentially sweeping over a set of
    parameters. Each concrete workflow must implement the `execute` method.
    """

    def __init__(self, name: str, description: str):
        """
        Initializes the base workflow.

        Args:
            name: A short, user-friendly name for the workflow.
            description: A longer description of what the workflow does.
        """
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, engine: QuantumEngine, **kwargs: Any) -> Dict[str, Any]:
        """
        Executes the full workflow.

        This method contains the core logic of the workflow, such as generating
        parameter sets, calling the appropriate API functions, and aggregating
        the results.

        Args:
            engine: The configured QuantumEngine to execute circuits on.
            **kwargs: Global keyword arguments that can be passed down to the
                      underlying experiments (e.g., `shots`).

        Returns:
            A dictionary containing the structured results of the entire workflow.
            The keys of the dictionary typically identify the specific run
            (e.g., by qubit), and the values are the result objects from the
            API calls.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"