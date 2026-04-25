from __future__ import annotations

from typing import Dict, List, Optional, Tuple, cast

from egm.circuits.circuit import QuantumCircuit
from egm.execution.executor import Executor
from egm.schemas.plan import CircuitTask, PlanSchema
from egm.schemas.results.execution import PlanExecutionResult, TaskExecutionResult


def run_plan(
    plan: PlanSchema,
    executor: Executor,
    default_shots: int = 1024,
) -> PlanExecutionResult:
    """
    Run a PlanSchema using the provided Executor.

    - No scheduler/job_manager/concurrency/retry.
    - Type-gates CircuitTask.circuits to List[QuantumCircuit].
    - Returns a minimal PlanExecutionResult with per-task TaskExecutionResult.
    """

    task_results: List[TaskExecutionResult] = []

    for task in plan.tasks:
        shots = cast(int, task.meta_data.get("shots", default_shots))

        circuits_obj = task.circuits
        if not isinstance(circuits_obj, list) or any(
            not isinstance(c, QuantumCircuit) for c in circuits_obj
        ):
            task_results.append(
                TaskExecutionResult(
                    plan_id=task.plan_id,
                    task_id=task.task_id,
                    status="type_error",
                    error=f"Expected List[QuantumCircuit], got {type(circuits_obj).__name__}.",
                    ideal_noisy_pairs=[],
                )
            )
            continue

        circuits = cast(List[QuantumCircuit], circuits_obj)
        try:
            pairs = executor.execute_with_ideal(circuits, shots=shots)
            task_results.append(
                TaskExecutionResult(
                    plan_id=task.plan_id,
                    task_id=task.task_id,
                    status="ok",
                    error=None,
                    ideal_noisy_pairs=pairs,
                )
            )
        except Exception as exc:
            task_results.append(
                TaskExecutionResult(
                    plan_id=task.plan_id,
                    task_id=task.task_id,
                    status="execution_error",
                    error=f"{type(exc).__name__}: {exc}",
                    ideal_noisy_pairs=[],
                )
            )

    return PlanExecutionResult(
        plan_id=plan.plan_id,
        backend_name=plan.backend_name,
        task_results=task_results,
    )

