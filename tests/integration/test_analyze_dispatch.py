"""Integration tests for unified analysis dispatch."""

from __future__ import annotations

import pytest

from egm.analysis import analyze_task_execution_result
from egm.schemas.plan import CircuitTask
from egm.schemas.results.execution import TaskExecutionResult
from tests.conftest import require_scipy


def _task(protocol: str, depth: int, num_qubits: int = 1) -> CircuitTask:
    return CircuitTask(
        plan_id="plan-test",
        task_id=f"task-{protocol}-{depth}",
        protocol=protocol,
        qubits=list(range(num_qubits)),
        number_of_circuits=1,
        meta_data={"depth": depth, "protocol": protocol},
    )


@pytest.mark.integration
def test_dispatch_xeb_ok():
    require_scipy()
    task = _task("XEB", depth=5)
    ideal = {"0": 0.5, "1": 0.5}
    noisy = {"0": 480, "1": 544}
    exec_result = TaskExecutionResult(
        plan_id=task.plan_id,
        task_id=task.task_id,
        status="ok",
        ideal_noisy_pairs=[(ideal, noisy)],
    )
    out = analyze_task_execution_result(task, exec_result)
    assert out.status == "ok"
    assert "xeb_analysis" in out.analysis_payload


@pytest.mark.integration
def test_dispatch_rb_ok():
    task = _task("RB", depth=10)
    exec_result = TaskExecutionResult(
        plan_id=task.plan_id,
        task_id=task.task_id,
        status="ok",
        ideal_noisy_pairs=[({"0": 0.0}, {"0": 900, "1": 124})],
    )
    out = analyze_task_execution_result(task, exec_result)
    assert out.status == "ok"
    assert "rb_analysis" in out.analysis_payload
    assert "survival_probability" in out.analysis_payload["rb_analysis"]


@pytest.mark.integration
def test_dispatch_unknown_protocol_error():
    task = _task("UNKNOWN_PROTO", depth=1)
    exec_result = TaskExecutionResult(
        plan_id=task.plan_id,
        task_id=task.task_id,
        status="ok",
        ideal_noisy_pairs=[({"0": 1.0}, {"0": 1000})],
    )
    out = analyze_task_execution_result(task, exec_result)
    assert out.status == "analysis_error"
