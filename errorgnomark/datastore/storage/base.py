# errorgnomark/datastore/storage/base.py

"""
Abstract base class for all storage backends.

This module defines the interface that all concrete storage implementations
must adhere to. This allows for a pluggable storage system where the backend
(e.g., SQLite, PostgreSQL, JSON file) can be easily swapped.
"""

# -------------------------------------------------------------------
# 1. Standard Library Imports
# -------------------------------------------------------------------
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

# -------------------------------------------------------------------
# 2. Internal Framework Imports
# -------------------------------------------------------------------
from ..models import ExperimentRun

# ==============================================================================
# Abstract Storage Interface
# ==============================================================================

class BaseStorage(ABC):
    """
    An abstract base class defining the interface for data storage.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establishes a connection to the data source."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Closes the connection to the data source."""
        pass

    @abstractmethod
    def save_run(self, run_data: ExperimentRun) -> ExperimentRun:
        """
        Saves a single ExperimentRun to the data store.

        Args:
            run_data: A Pydantic model instance of the experiment run.

        Returns:
            The saved ExperimentRun, potentially updated with a database-assigned ID
            or timestamp.
        """
        pass

    @abstractmethod
    def get_run_by_id(self, run_id: UUID) -> Optional[ExperimentRun]:
        """
        Retrieves a single experiment run by its unique ID.

        Args:
            run_id: The UUID of the experiment run.

        Returns:
            An ExperimentRun model instance if found, otherwise None.
        """
        pass

    @abstractmethod
    def find_runs(self, query_filters: Optional[Dict[str, Any]] = None) -> List[ExperimentRun]:
        """
        Finds experiment runs that match a set of filters.

        Args:
            query_filters: A dictionary of fields and values to filter by.
                           Example: {'protocol_name': 'StandardRB', 'tags.user': 'alice'}

        Returns:
            A list of matching ExperimentRun model instances.
        """
        pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()