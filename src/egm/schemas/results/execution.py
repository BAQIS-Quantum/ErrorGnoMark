from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class TaskExecutionResult:
    """
    Minimal execution result contract for one CircuitTask.

    status values (string policy):
      - "ok"
      - "type_error"
      - "execution_error"
    """

    plan_id: str
    task_id: str
    status: str
    error: Optional[str] = None
    ideal_noisy_pairs: List[Tuple[Dict[str, float], Dict[str, int]]] = field(default_factory=list)


@dataclass(frozen=True)
class PlanExecutionResult:
    """
    Minimal execution result contract for a whole PlanSchema.

    No top-level status; caller can derive from task_results.
    """

    plan_id: str
    backend_name: str
    task_results: List[TaskExecutionResult] = field(default_factory=list)

