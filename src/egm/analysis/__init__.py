"""
egm.analysis — Unified analysis dispatch.

Provides `analyze_task_execution_result` as the single task-level entrypoint
that routes to protocol-specific analyzers based on `task.protocol`.
"""

from __future__ import annotations

from typing import Dict, Any, List

from egm.schemas.plan import CircuitTask
from egm.schemas.results.analysis import TaskAnalysisResult
from egm.schemas.results.execution import TaskExecutionResult


def _analyze_xeb_task(task: CircuitTask, exec_result: TaskExecutionResult) -> TaskAnalysisResult:
    from egm.analysis.xeb import analyze_xeb_and_spb_from_results

    depth = task.meta_data.get("depth")
    if depth is None:
        return TaskAnalysisResult(
            plan_id=task.plan_id, task_id=task.task_id,
            status="analysis_error",
            error="Task depth is None; cannot build results_by_depth.",
            analysis_payload={},
        )
    if not exec_result.ideal_noisy_pairs:
        return TaskAnalysisResult(
            plan_id=task.plan_id, task_id=task.task_id,
            status="analysis_error",
            error="ideal_noisy_pairs is empty; cannot analyze.",
            analysis_payload={},
        )

    results_by_depth = {int(depth): exec_result.ideal_noisy_pairs}
    num_qubits = len(task.qubits)
    payload = analyze_xeb_and_spb_from_results(
        results_by_depth=results_by_depth,
        num_qubits=num_qubits,
    )
    if not isinstance(payload, dict) or not payload:
        return TaskAnalysisResult(
            plan_id=task.plan_id, task_id=task.task_id,
            status="analysis_error",
            error="Analysis returned empty or non-dict payload.",
            analysis_payload={},
        )
    return TaskAnalysisResult(
        plan_id=task.plan_id, task_id=task.task_id,
        status="ok", error=None,
        analysis_payload=payload,
    )


def _analyze_rb_task(task: CircuitTask, exec_result: TaskExecutionResult) -> TaskAnalysisResult:
    """
    RB task-level analysis: compute survival probability at this depth.

    Full curve fitting (EPC) requires multi-depth aggregation and is handled
    by `analyze_rb_standard` at the batch level via AnalysisFactory.
    """
    depth = task.meta_data.get("depth")
    if depth is None:
        return TaskAnalysisResult(
            plan_id=task.plan_id, task_id=task.task_id,
            status="analysis_error",
            error="Task depth is None.",
            analysis_payload={},
        )
    if not exec_result.ideal_noisy_pairs:
        return TaskAnalysisResult(
            plan_id=task.plan_id, task_id=task.task_id,
            status="analysis_error",
            error="ideal_noisy_pairs is empty; cannot analyze.",
            analysis_payload={},
        )

    num_qubits = len(task.qubits)
    ground_state = "0" * num_qubits

    survivals = []
    for _ideal, noisy in exec_result.ideal_noisy_pairs:
        total = sum(noisy.values())
        if total > 0:
            survivals.append(noisy.get(ground_state, 0) / total)
        else:
            survivals.append(0.0)

    import numpy as np
    mean_survival = float(np.mean(survivals)) if survivals else 0.0
    std_survival = float(np.std(survivals, ddof=1) / np.sqrt(len(survivals))) if len(survivals) > 1 else 0.0

    payload: Dict[str, Any] = {
        "rb_analysis": {
            "depth": int(depth),
            "num_qubits": num_qubits,
            "survival_probability": mean_survival,
            "survival_std_error": std_survival,
            "num_samples": len(survivals),
        }
    }
    return TaskAnalysisResult(
        plan_id=task.plan_id, task_id=task.task_id,
        status="ok", error=None,
        analysis_payload=payload,
    )


_TASK_ANALYZERS = {
    "XEB": _analyze_xeb_task,
    "RB": _analyze_rb_task,
}


def analyze_task_execution_result(
    task: CircuitTask, exec_result: TaskExecutionResult
) -> TaskAnalysisResult:
    """
    Unified task-level analysis entrypoint.

    Routes to the correct protocol analyzer based on task.protocol (or
    task.meta_data["protocol"]).  Extensible via _TASK_ANALYZERS registry.
    """
    if exec_result.status != "ok":
        return TaskAnalysisResult(
            plan_id=task.plan_id, task_id=task.task_id,
            status="analysis_error",
            error=f"Task execution status is '{exec_result.status}', not eligible for analysis.",
            analysis_payload={},
        )

    protocol = (task.protocol or task.meta_data.get("protocol", "")).upper()
    protocol_base = protocol.split("_")[0]

    analyzer_fn = _TASK_ANALYZERS.get(protocol_base)
    if analyzer_fn is None:
        return TaskAnalysisResult(
            plan_id=task.plan_id, task_id=task.task_id,
            status="analysis_error",
            error=f"No task-level analyzer registered for protocol '{protocol}'.",
            analysis_payload={},
        )

    try:
        return analyzer_fn(task, exec_result)
    except Exception as exc:
        return TaskAnalysisResult(
            plan_id=task.plan_id, task_id=task.task_id,
            status="analysis_error",
            error=f"{type(exc).__name__}: {exc}",
            analysis_payload={},
        )
