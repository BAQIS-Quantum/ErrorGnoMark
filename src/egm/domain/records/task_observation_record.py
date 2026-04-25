from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from egm.schemas.plan import CircuitTask
from egm.schemas.results.execution import TaskExecutionResult
from egm.schemas.results.analysis import TaskAnalysisResult


@dataclass(frozen=True)
class TaskObservationRecord:
    # identity / lineage
    task_id: str
    plan_id: Optional[str]

    # query keys
    protocol: str
    qubits: List[int]
    depth: Optional[int]
    shots: Optional[int]
    backend_name: Optional[str]
    chip_name: Optional[str]

    # stage status
    execution_status: str
    execution_error: Optional[str]
    analysis_status: str
    analysis_error: Optional[str]

    # payload
    execution_summary: Dict[str, Any] = field(default_factory=dict)
    analysis_payload: Dict[str, Any] = field(default_factory=dict)

    # time
    observation_time: Optional[datetime] = None


def to_task_observation_record(
    task: CircuitTask,
    exec_result: TaskExecutionResult,
    analysis_result: TaskAnalysisResult,
) -> TaskObservationRecord:
    """
    Pure mapping from workflow outputs to a query-facing task-level observation record.

    - Task context comes from CircuitTask (+ meta_data).
    - Execution status comes from TaskExecutionResult.
    - Analysis status/payload comes from TaskAnalysisResult.
    """

    if task.task_id != exec_result.task_id:
        raise ValueError(
            f"task.task_id != exec_result.task_id ({task.task_id!r} != {exec_result.task_id!r})"
        )
    if task.task_id != analysis_result.task_id:
        raise ValueError(
            f"task.task_id != analysis_result.task_id ({task.task_id!r} != {analysis_result.task_id!r})"
        )

    if task.plan_id != exec_result.plan_id:
        raise ValueError(
            f"task.plan_id != exec_result.plan_id ({task.plan_id!r} != {exec_result.plan_id!r})"
        )
    if task.plan_id != analysis_result.plan_id:
        raise ValueError(
            f"task.plan_id != analysis_result.plan_id ({task.plan_id!r} != {analysis_result.plan_id!r})"
        )

    depth = task.meta_data.get("depth")
    shots = task.meta_data.get("shots")
    backend_name = task.meta_data.get("backend_name")
    chip_name = task.meta_data.get("chip_name")

    observation_time = task.meta_data.get("observation_time")
    if observation_time is not None and not isinstance(observation_time, datetime):
        raise ValueError(
            "meta_data['observation_time'] must be a datetime if provided."
        )

    execution_summary: Dict[str, Any] = {
        "num_pairs": len(exec_result.ideal_noisy_pairs),
        "pairs_digest": None,
        "artifact_ref": None,
    }

    return TaskObservationRecord(
        task_id=task.task_id,
        plan_id=task.plan_id,
        protocol=task.protocol,
        qubits=task.qubits,
        depth=depth,
        shots=shots,
        backend_name=backend_name,
        chip_name=chip_name,
        execution_status=exec_result.status,
        execution_error=exec_result.error,
        analysis_status=analysis_result.status,
        analysis_error=analysis_result.error,
        execution_summary=execution_summary,
        analysis_payload=analysis_result.analysis_payload,
        observation_time=observation_time,
    )

