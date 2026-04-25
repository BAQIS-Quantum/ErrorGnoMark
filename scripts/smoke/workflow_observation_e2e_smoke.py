from __future__ import annotations

from egm.analysis.xeb import analyze_task_execution_result
from egm.backends.base_backend import BaseBackend
from egm.circuits.circuit import QuantumCircuit
from egm.datastore.observation_store_memory import InMemoryObservationStore
from egm.execution.executor import Executor
from egm.execution.plan_runner import run_plan
from egm.schemas.configs import (
    ConfigBase,
    ConfigSchema,
    HardwareConfig,
    ProtocolBundle,
    ProtocolConfig,
)
from egm.services.planning.plan_builder import PlanBuilder
from egm.services.queries.observation_query_service import ObservationQueryService
from egm.services.serialization.observation_record import to_persistence_observation_dict
from egm.domain.records.task_observation_record import to_task_observation_record


class LocalCountsBackend(BaseBackend):
    """
    Minimal backend stub to avoid hardware dependencies.

    It returns deterministic-ish counts; the ideal reference probabilities are
    computed by Executor's internal IdealBackend.
    """

    def __init__(self) -> None:
        super().__init__(name="LocalCountsBackend")

    def run(self, circuit: QuantumCircuit, shots=None):
        n = circuit.num_qubits
        shots_i = int(shots or 10)
        return None, {("0" * n): shots_i}


def _print_header(
    *,
    protocol: str,
    backend_name: str,
    chip_name: str,
    qubits: list[int],
    depths: list[int],
    shots: int,
    repeats: int,
    plan_task_count: int | None,
) -> None:
    print("=" * 60)
    print("EGM Workflow E2E Smoke")
    print("=" * 60)
    print(f"protocol           : {protocol}")
    print(f"backend            : {backend_name}")
    print(f"chip               : {chip_name}")
    print(f"qubits             : {qubits}")
    print(f"depths             : {depths}")
    print(f"shots              : {shots}")
    print(f"repeats            : {repeats}")
    if plan_task_count is not None:
        print(f"plan task count    : {plan_task_count}")
    print("=" * 60)
    print()


def _stage(i: int, total: int, msg: str) -> None:
    print(f"[{i}/{total}] {msg} ...")


def _ok(msg: str) -> None:
    print(f"[ok ] {msg}")


def _warn(msg: str) -> None:
    print(f"[warn] {msg}")


def main() -> None:
    total_stages = 7

    protocol = "XEB"
    backend_name = "LocalCountsBackend"
    chip_name = "chip-alpha"
    qubits = [0, 1]
    depths = [3]
    shots = 10
    repeats = 1

    _print_header(
        protocol=protocol,
        backend_name=backend_name,
        chip_name=chip_name,
        qubits=qubits,
        depths=depths,
        shots=shots,
        repeats=repeats,
        plan_task_count=None,
    )

    _stage(1, total_stages, "building config")
    config = ConfigSchema(
        base=ConfigBase(plan_id="plan-e2e-1", backend_name=backend_name),
        hardware=HardwareConfig(chip_name=chip_name, gate_set="native", noise_flags={}),
        protocol=ProtocolConfig(
            number_of_circuits=repeats,
            shots=shots,
            bundles=[ProtocolBundle(protocol=protocol, qubits=[qubits], depths=depths)],
        ),
    )
    _ok("config built")

    _stage(2, total_stages, "building plan")
    plan = PlanBuilder.build_plan_from_config(config)
    assert plan.tasks, "Expected non-empty plan.tasks"
    _ok(f"plan built: {len(plan.tasks)} task(s)")
    assert all(isinstance(c, QuantumCircuit) for t in plan.tasks for c in t.circuits)

    # Task summary (first 3 tasks)
    for idx, task in enumerate(plan.tasks[:3], start=1):
        t_depth = task.meta_data.get("depth")
        t_shots = task.meta_data.get("shots")
        t_backend = task.meta_data.get("backend_name")
        t_chip = task.meta_data.get("chip_name")
        print()
        print(f"[task {idx}/{len(plan.tasks)}]")
        print(f"  task_id          : {task.task_id}")
        print(f"  protocol         : {task.protocol}")
        if t_backend is not None:
            print(f"  backend          : {t_backend}")
        if t_chip is not None:
            print(f"  chip             : {t_chip}")
        print(f"  qubits           : {task.qubits}")
        if t_depth is not None:
            print(f"  depth            : {t_depth}")
        if t_shots is not None:
            print(f"  shots            : {t_shots}")
        print(f"  repeats          : {repeats}")

    print()
    _stage(3, total_stages, "running plan")
    executor = Executor(LocalCountsBackend())
    exec_res = run_plan(plan, executor)
    assert exec_res.task_results, "Expected non-empty task_results"
    _ok(f"tasks executed: {len(exec_res.task_results)}")

    # execution status summary
    status_counts: dict[str, int] = {}
    for tr in exec_res.task_results:
        status_counts[tr.status] = status_counts.get(tr.status, 0) + 1

    print()
    _stage(4, total_stages, "analyzing results")
    observations = []
    warned_spb_fit = False
    for task, tr in zip(plan.tasks, exec_res.task_results):
        ar = analyze_task_execution_result(task, tr)
        obs = to_task_observation_record(task, tr, ar)
        observations.append(obs)

        # Friendly warning summary (best-effort)
        payload = ar.analysis_payload or {}
        spb_fit = (
            payload.get("spb_analysis", {}) if isinstance(payload, dict) else {}
        )
        spb_fit_results = (
            spb_fit.get("fit_results", {}) if isinstance(spb_fit, dict) else {}
        )
        msg = spb_fit_results.get("message")
        if isinstance(msg, str) and "Insufficient points (<3)" in msg:
            warned_spb_fit = True

    assert observations, "Expected at least one TaskObservationRecord"
    if warned_spb_fit:
        _warn("SPB fit skipped because insufficient points (<3)")
    _ok(f"observations built: {len(observations)}")

    print()
    _stage(5, total_stages, "converting observations")
    persistence_dicts = [to_persistence_observation_dict(o) for o in observations]
    assert persistence_dicts, "Expected at least one persistence dict"
    _ok(f"persistence payloads built: {len(persistence_dicts)}")

    print()
    _stage(6, total_stages, "saving to store")
    store = InMemoryObservationStore()
    svc = ObservationQueryService(store=store)
    ids = [store.save_observation(d) for d in persistence_dicts]
    assert ids, "Expected at least one observation_id"
    _ok(f"observations saved: {len(ids)}")

    print()
    _stage(7, total_stages, "querying observations")
    got0 = svc.get_observation(ids[0])
    assert got0 is not None, "Expected get_observation hit"
    _ok("get_observation hit")
    assert got0.get("task_id"), "Expected task_id in observation"
    assert got0.get("protocol"), "Expected protocol in observation"
    assert got0.get("backend_name"), "Expected backend_name in observation"

    all_obs = svc.list_observations()
    assert len(all_obs) > 0, "Expected non-empty list_observations"
    _ok(f"list_observations returned {len(all_obs)} item(s)")

    filtered = svc.filter_observations(protocol=got0["protocol"])
    assert filtered, "Expected non-empty filter_observations(protocol=...)"
    _ok(
        f"filter_observations(protocol='{got0['protocol']}') returned {len(filtered)} item(s)"
    )

    missing = svc.get_observation("does-not-exist")
    assert missing is None, "Expected missing id -> None"

    print()
    print("[result summary]")
    print(f"  tasks executed   : {len(exec_res.task_results)}")
    print(f"  observations     : {len(observations)}")
    print(f"  saved            : {len(ids)}")
    print(f"  execution status : {status_counts}")
    print()
    print("[sample observation]")
    sample_id = ids[0]
    print(f"  id               : {sample_id}")
    print(f"  task_id          : {got0.get('task_id')}")
    print(f"  protocol         : {got0.get('protocol')}")
    print(f"  backend          : {got0.get('backend_name')}")
    print(f"  chip             : {got0.get('chip_name')}")
    print(f"  qubits           : {got0.get('qubits')}")
    print()
    print("workflow observation e2e smoke passed")


if __name__ == "__main__":
    main()

