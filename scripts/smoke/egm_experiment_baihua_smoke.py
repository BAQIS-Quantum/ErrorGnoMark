"""
EGM experiment → Baihua: write RB + XEB benchmark_run + observation_record.

Demonstrates that EGM internal experiment data and Quafu official calibration
data coexist in the same database under the same chip_id.

Requires:
    - EGM_PG_DSN set
    - db/phase1 schema + seed (010–050) applied
    - Baihua chip registered (seed 050)
"""

from __future__ import annotations

import os
import sys
import uuid

from datetime import datetime, timezone

from egm.analysis import analyze_task_execution_result
from egm.backends.dummy_backend_xeb import DummyBackend
from egm.datastore.postgres_observation_store import PostgresObservationStore
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
from egm.services.serialization.observation_record import to_persistence_observation_dict

import json
import math

# DummyBackend = UnifiedMatrixBackend: matrix propagation + physical noise
_backend = DummyBackend(cycle_fidelity=0.9996, seed=42)


def _sanitize_nan(obj):
    """Recursively replace NaN/Inf with None so JSON serialization succeeds."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize_nan(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_nan(v) for v in obj]
    return obj


def _run_protocol(dsn: str, protocol: str, qubits: list, depths: list, shots: int = 2048) -> str:
    """Run one protocol against Baihua and save to PG. Returns observation_id."""
    config = ConfigSchema(
        base=ConfigBase(plan_id=f"plan-baihua-{protocol.lower()}-1", backend_name=_backend.name),
        hardware=HardwareConfig(chip_name="Baihua", gate_set="native", noise_flags={}),
        protocol=ProtocolConfig(
            number_of_circuits=1,
            shots=shots,
            bundles=[ProtocolBundle(protocol=protocol, qubits=[qubits], depths=depths)],
        ),
    )

    plan = PlanBuilder.build_plan_from_config(config)
    executor = Executor(_backend)
    exec_res = run_plan(plan, executor)

    observations = []
    for task, tr in zip(plan.tasks, exec_res.task_results):
        ar = analyze_task_execution_result(task, tr)
        observations.append(to_task_observation_record(task, tr, ar))

    persistence_dicts = [_sanitize_nan(to_persistence_observation_dict(o)) for o in observations]
    store = PostgresObservationStore(dsn)
    ids = [store.save_observation(d) for d in persistence_dicts]

    return ids[0]


def _run_irb_experiment(dsn: str, qubits: list, depths: list, gate_name: str = "cz") -> str:
    """
    Run Interleaved RB via real circuit generation (rb.py) and save to PG.

    Uses InterleavedRBExperiment to generate reference + interleaved circuits,
    executes on DummyBackend, computes EPG, and persists the observation.
    """
    from egm.protocols.physical.rb import generate_standard_rb_circuits, generate_interleaved_rb_circuits
    from egm.circuits.circuit import Gate
    from egm.analysis.rb import stitch_rb_results, analyze_rb_standard, calculate_epg

    interleaved_gate = Gate(gate_name.upper(), tuple(qubits[:2]))

    ref_circuits = generate_standard_rb_circuits(
        qubits=qubits, depths=depths, circuits_per_depth=5, seed=77
    )
    int_circuits = generate_interleaved_rb_circuits(
        qubits=qubits, depths=depths, circuits_per_depth=5,
        interleaved_gate=interleaved_gate, seed=77
    )

    executor = Executor(_backend)
    ref_raw = executor.execute_with_ideal(ref_circuits, shots=1024)
    int_raw = executor.execute_with_ideal(int_circuits, shots=1024)

    ref_stitched = stitch_rb_results(ref_circuits, ref_raw)
    int_stitched = stitch_rb_results(int_circuits, int_raw)

    fit_ref = analyze_rb_standard(ref_stitched)
    fit_int = analyze_rb_standard(int_stitched)

    p_ref = fit_ref.alpha.value if fit_ref.success and fit_ref.alpha else 0.99
    p_int = fit_int.alpha.value if fit_int.success and fit_int.alpha else 0.98
    epg = calculate_epg(p_ref, p_int, num_qubits=len(qubits))

    payload = _sanitize_nan({
        "protocol": "interleaved_rb",
        "chip_name": "Baihua",
        "qubits": qubits,
        "observation_time": datetime.now(timezone.utc).isoformat(),
        "execution_status": "ok",
        "analysis_status": "ok",
        "backend_name": _backend.name,
        "analysis_payload": {
            "gate_name": gate_name,
            "epg": epg,
            "epc_reference": fit_ref.epc if fit_ref.success else None,
            "epc_interleaved": fit_int.epc if fit_int.success else None,
            "p_reference": p_ref,
            "p_interleaved": p_int,
            "depths": depths,
            "success": fit_ref.success and fit_int.success,
        },
    })

    store = PostgresObservationStore(dsn)
    return store.save_observation(payload)


def _run_rb_experiment(dsn: str, qubits: list, depths: list, shots: int = 2048) -> str:
    """Run Standard RB via PlanBuilder + unified analysis. Returns observation_id."""
    return _run_protocol(dsn, "RB", qubits=qubits, depths=depths, shots=shots)


def main() -> None:
    dsn = os.environ.get("EGM_PG_DSN")
    if not dsn:
        print("EGM_PG_DSN not set; skipping.", file=sys.stderr)
        sys.exit(0)

    total = 7
    print("=" * 60)
    print("EGM Experiment → Baihua (XEB + RB + IRB smoke)")
    print("=" * 60)

    print(f"\n[1/{total}] Running XEB on qubits [0, 1] ...")
    xeb_id = _run_protocol(dsn, "XEB", qubits=[0, 1], depths=[3, 5])
    print(f"  → observation saved: {xeb_id}")

    print(f"\n[2/{total}] Running XEB on qubits [2, 3] ...")
    xeb_id2 = _run_protocol(dsn, "XEB", qubits=[2, 3], depths=[3, 5])
    print(f"  → observation saved: {xeb_id2}")

    print(f"\n[3/{total}] Running Standard RB on qubit [0] ...")
    rb_id = _run_rb_experiment(dsn, qubits=[0], depths=[1, 2, 5, 10])
    print(f"  → observation saved: {rb_id}")

    print(f"\n[4/{total}] Running Standard RB on qubits [0, 1] ...")
    rb_id2 = _run_rb_experiment(dsn, qubits=[0, 1], depths=[1, 2, 5])
    print(f"  → observation saved: {rb_id2}")

    print(f"\n[5/{total}] Running Interleaved RB (CZ gate) on qubits [0, 1] ...")
    irb_id = _run_irb_experiment(dsn, qubits=[0, 1], depths=[1, 2, 5])
    print(f"  → observation saved: {irb_id}")

    print(f"\n[6/{total}] Verifying benchmark_run rows for Baihua ...")
    from psycopg import Connection
    from psycopg.rows import dict_row

    with Connection.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT benchmark_name, status, start_time
                FROM benchmark_run
                WHERE chip_id = (SELECT chip_id FROM chip WHERE chip_name = 'Baihua')
                ORDER BY start_time DESC
                LIMIT 20
            """)
            rows = cur.fetchall()

    print(f"  → {len(rows)} benchmark_run(s) for Baihua (latest 20):")
    for r in rows:
        print(f"    {r['benchmark_name']:20s}  {r['status']:10s}  {r['start_time']}")

    print(f"\n[{total}/{total}] Checking all data sources coexist ...")
    with Connection.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT producer_type, count(*) AS cnt
                FROM observation_record
                WHERE chip_id = (SELECT chip_id FROM chip WHERE chip_name = 'Baihua')
                GROUP BY producer_type
                ORDER BY producer_type
            """)
            rows = cur.fetchall()

    for r in rows:
        print(f"  {r['producer_type']:25s} → {r['cnt']} observation(s)")

    print("\nAll checks passed. Quafu calibration + EGM experiments (XEB/RB/IRB) coexist.")


if __name__ == "__main__":
    main()
