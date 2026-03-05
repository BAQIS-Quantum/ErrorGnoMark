# egm/datastore/base.py

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class BaseExperimentStore(ABC):
    """
    Abstract interface for experiment lifecycle management.

    This subsystem is responsible for:
        - registering experiment runs
        - storing artifacts
        - retrieving historical results
        - managing experiment metadata

    Concrete implementations may use SQLite, file storage, or cloud backends.
    """

    @abstractmethod
    def register(self, metadata: dict) -> UUID:
        """Register a new experiment run and return its UUID."""
        pass

    @abstractmethod
    def save_result(self, run_id: UUID, result: Any) -> None:
        """Persist experiment result."""
        pass

    @abstractmethod
    def load_result(self, run_id: UUID) -> Any:
        """Load stored result."""
        pass


"""
Datastore Subsystem
===================

Purpose
-------
The datastore subsystem is responsible for experiment lifecycle
management and persistent data handling within the EGM system.

It is NOT a generic data container.
It is a structured experiment management subsystem.

This module is currently a placeholder for future implementation.
Concrete logic will be introduced when large-scale experiment
tracking, reproducibility, and lineage management become necessary.


Architectural Position
----------------------
Layer: L6 – Orchestration Layer

The datastore subsystem operates at the orchestration level.
It may depend on:
    - domain models
    - schemas

It must NOT be depended upon by:
    - foundation
    - engine
    - experiments

Dependency direction:

    Suites  →  Datastore
    Datastore → Domain / Schemas


Subsystem Responsibilities
--------------------------

1. Experiment Registry
   - Register experiment runs
   - Generate unique identifiers (UUID)
   - Store metadata (timestamp, backend, config version, etc.)

2. Artifact Storage
   - Persist raw experiment outputs
   - Persist processed analysis results
   - Store circuit dumps or serialized configs

3. Version Tracking
   - Record experiment configuration versions
   - Track backend versions
   - Track software revision information
   - Enable reproducibility

4. Lineage Management (Optional Advanced Feature)
   - Record experiment derivation relationships
   - Support parent-child experiment graphs
   - Enable reproducibility tracing

5. Query Interface
   - Query experiments by:
        * backend
        * date range
        * experiment type
        * performance metrics
   - Enable statistical aggregation across runs


Planned Module Structure
-------------------------

egm/datastore/

    registry.py
        Handles experiment registration and metadata indexing.

    artifacts.py
        Manages artifact persistence and retrieval.

    versioning.py
        Handles configuration and software version tracking.

    lineage.py
        (Optional) Manages experiment derivation graphs.

    query.py
        Provides structured query interface over stored experiments.

    backends/
        Storage backend implementations:

            sqlite_store.py
                Local relational database storage.

            file_store.py
                Filesystem-based storage.

            s3_store.py
                Cloud-based object storage.


Design Principles
-----------------

- Clear separation from domain modeling.
- No execution logic.
- No backend-specific computation.
- Interface-first design.
- Pluggable storage backend architecture.
- Reproducibility and traceability oriented.


Development Strategy
--------------------

This subsystem will remain minimal until:
    - large-scale experiment tracking is required
    - experiment reproducibility becomes critical
    - cross-experiment statistical analysis is needed

Implementation should be demand-driven, not speculative.

"""