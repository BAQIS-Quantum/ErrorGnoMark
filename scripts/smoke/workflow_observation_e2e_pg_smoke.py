"""
PostgreSQL variant of workflow observation E2E smoke.

- ``EGM_PG_DSN`` unset: exit 0 (no DB).
- ``EGM_PG_DSN`` set: requires ``psycopg`` + applied ``db/phase1`` schema and seed.
"""
from __future__ import annotations

import os
import uuid

from egm.analysis.xeb import analyze_task_execution_result
from egm.backends.base_backend import BaseBackend
from egm.circuits.circuit import QuantumCircuit
from egm.datastore.postgres_observation_store import PostgresObservationStore, resolve_chip_id_for_smoke
from egm.domain.records.task_observation_record import to_task_observation_record
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


class LocalCountsBackend(BaseBackend):
    """Minimal backend stub (same as workflow_observation_e2e_smoke)."""

    def __init__(self) -> None:
        super().__init__(name="LocalCountsBackend")

    def run(self, circuit: QuantumCircuit, shots=None):
        n = circuit.num_qubits
        shots_i = int(shots or 10)
        return None, {("0" * n): shots_i}


def _stage(i: int, total: int, msg: str) -> None:
    print(f"[{i}/{total}] {msg} ...")


def _ok(msg: str) -> None:
    print(f"[ok ] {msg}")


def main() -> None:
    dsn = os.environ.get("EGM_PG_DSN")
    if not dsn:
        print("EGM_PG_DSN not set; skip workflow_observation_e2e_pg_smoke")
        return

    try:
        from psycopg import Connection
        from psycopg.rows import dict_row
    except ImportError as e:
        raise SystemExit(
            "EGM_PG_DSN is set but psycopg is not installed. "
            "pip install 'psycopg[binary]>=3.2'"
        ) from e

    expected_chip_id = resolve_chip_id_for_smoke(dsn, "chip-alpha")
    total_stages = 8

    print("=" * 60)
    print("EGM Workflow E2E Smoke (PostgresObservationStore)")
    print("=" * 60)

    _stage(1, total_stages, "building config")
    config = ConfigSchema(
        base=ConfigBase(plan_id="plan-e2e-pg-1", backend_name="LocalCountsBackend"),
        hardware=HardwareConfig(chip_name="chip-alpha", gate_set="native", noise_flags={}),
        protocol=ProtocolConfig(
            number_of_circuits=1,
            shots=10,
            bundles=[ProtocolBundle(protocol="XEB", qubits=[[0, 1]], depths=[3])],
        ),
    )
    _ok("config built")

    _stage(2, total_stages, "building plan")
    plan = PlanBuilder.build_plan_from_config(config)
    assert plan.tasks
    _ok(f"plan built: {len(plan.tasks)} task(s)")
    assert all(isinstance(c, QuantumCircuit) for t in plan.tasks for c in t.circuits)

    _stage(3, total_stages, "running plan")
    executor = Executor(LocalCountsBackend())
    exec_res = run_plan(plan, executor)
    assert exec_res.task_results
    _ok(f"tasks executed: {len(exec_res.task_results)}")

    _stage(4, total_stages, "analyzing results")
    observations = []
    for task, tr in zip(plan.tasks, exec_res.task_results):
        ar = analyze_task_execution_result(task, tr)
        observations.append(to_task_observation_record(task, tr, ar))
    assert observations
    _ok(f"observations built: {len(observations)}")

    _stage(5, total_stages, "converting observations")
    persistence_dicts = [to_persistence_observation_dict(o) for o in observations]
    _ok(f"persistence payloads built: {len(persistence_dicts)}")

    _stage(6, total_stages, "saving to PostgresObservationStore")
    store = PostgresObservationStore(dsn)
    svc = ObservationQueryService(store=store)
    ids = [store.save_observation(d) for d in persistence_dicts]
    _ok(f"observations saved: {len(ids)}")

    _stage(7, total_stages, "querying observations (PG)")
    got0 = svc.get_observation(ids[0])
    assert got0 is not None
    assert got0.get("chip_name") == "chip-alpha"
    assert got0.get("protocol") == "XEB"
    _ok("get_observation hit")

    filtered = svc.filter_observations(protocol=got0["protocol"])
    assert filtered
    _ok("filter_observations(protocol=...) hit")

    _stage(8, total_stages, "verifying benchmark_run chip_id")
    oid_uuid = str(uuid.UUID(hex=ids[0]))
    with Connection.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT br.chip_id::text AS chip_id
                FROM benchmark_run br
                JOIN observation_record ob
                  ON ob.producer_id = br.benchmark_run_id
                 AND ob.producer_type = 'benchmark_run'
                WHERE ob.observation_record_id = %(oid)s::uuid
                LIMIT 1
                """,
                {"oid": oid_uuid},
            )
            row = cur.fetchone()
    assert row is not None
    assert row["chip_id"] == expected_chip_id, (row["chip_id"], expected_chip_id)
    _ok("benchmark_run chip_id matches seeded chip-alpha")

    print()
    print("workflow observation e2e pg smoke passed")


if __name__ == "__main__":
    main()
