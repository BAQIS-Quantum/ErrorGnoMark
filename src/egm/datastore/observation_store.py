"""
ObservationStore — observation record persistence contract.

This module defines the minimal store interface and the persistence payload shape
for observation records.

IMPORTANT:
- Datastore must NOT depend on egm.domain.* (domain records).
- This module defines contracts only; no drivers/DB/DDL/query logic here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, runtime_checkable


ObservationPersistenceDict = Dict[str, Any]


@dataclass(frozen=True)
class ObservationKeys:
    """
    Key policy for ObservationPersistenceDict.

    First version uses a plain dict; keys are centralized here to reduce drift.
    """

    # Structured top-level keys
    task_id: str = "task_id"
    plan_id: str = "plan_id"
    protocol: str = "protocol"
    depth: str = "depth"
    shots: str = "shots"
    backend_name: str = "backend_name"
    chip_name: str = "chip_name"
    execution_status: str = "execution_status"
    analysis_status: str = "analysis_status"
    execution_error: str = "execution_error"
    analysis_error: str = "analysis_error"
    observation_time: str = "observation_time"  # ISO 8601 string or None

    # Payload top-level keys
    qubits: str = "qubits"
    execution_summary: str = "execution_summary"
    analysis_payload: str = "analysis_payload"


KEYS = ObservationKeys()


@runtime_checkable
class ObservationStore(Protocol):
    """
    Minimal observation store interface.

    The store is responsible for generating observation_id.
    """

    def save_observation(self, record: ObservationPersistenceDict) -> str: ...

    def load_observation(self, observation_id: str) -> Optional[ObservationPersistenceDict]: ...

    def list_observation_ids(self) -> list[str]: ...

