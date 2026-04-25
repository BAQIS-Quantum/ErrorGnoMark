from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from egm.datastore.observation_store import KEYS, ObservationPersistenceDict
from egm.domain.records.task_observation_record import TaskObservationRecord


def to_persistence_observation_dict(
    record: TaskObservationRecord,
) -> ObservationPersistenceDict:
    """
    Serialize a domain TaskObservationRecord into a persistence payload dict.

    Rules:
    - observation_time is serialized as ISO 8601 string, or None.
    - analysis_payload and execution_summary are carried as-is.
    - This function is domain->persistence glue and must not live in datastore/.
    """

    obs_time = record.observation_time
    if obs_time is None:
        obs_time_str = None
    elif isinstance(obs_time, datetime):
        obs_time_str = obs_time.isoformat()
    else:
        raise ValueError("record.observation_time must be datetime|None")

    payload: Dict[str, Any] = {
        # Structured keys
        KEYS.task_id: record.task_id,
        KEYS.plan_id: record.plan_id,
        KEYS.protocol: record.protocol,
        KEYS.depth: record.depth,
        KEYS.shots: record.shots,
        KEYS.backend_name: record.backend_name,
        KEYS.chip_name: record.chip_name,
        KEYS.execution_status: record.execution_status,
        KEYS.analysis_status: record.analysis_status,
        KEYS.execution_error: record.execution_error,
        KEYS.analysis_error: record.analysis_error,
        KEYS.observation_time: obs_time_str,
        # Payload keys
        KEYS.qubits: list(record.qubits),
        KEYS.execution_summary: dict(record.execution_summary),
        KEYS.analysis_payload: dict(record.analysis_payload),
    }
    return payload

