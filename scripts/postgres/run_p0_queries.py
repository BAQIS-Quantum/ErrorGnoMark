#!/usr/bin/env python3
"""
Run Phase 1 demo SQL under sql/queries/p0/ against EGM_PG_DSN.

Covers Q1–Q23 demo slice (including **Q7** window/paging on API-06, **Q8** on API-07, **Q12** on API-10,
**Q14** on API-11) plus **filtered** variants for API-15/16. See p1-step2 API-01..16.

Requires psycopg. Skips with exit 0 when EGM_PG_DSN unset (local/CI without DB).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from egm.datastore.phase1_pg_constants import (
    BENCHMARK_RUN_SEED_DEMO_ID,
    BENCHMARK_RUN_SEED_RB_LATEST_ID,
    CALIBRATION_ARTIFACT_READOUT_SEED_ID,
    CALIBRATION_RUN_ALPHA_GATE_SEED_ID,
    CALIBRATION_RUN_ALPHA_READOUT_SEED_ID,
    CALIBRATION_SNAPSHOT_ALPHA_LATEST_ID,
    CALIBRATION_SNAPSHOT_ALPHA_SUPERSEDED_ID,
    CHIP_ALPHA_ID,
    LINEAGE_EDGE_CALIBRATION_INPUT_ID,
    LINEAGE_EDGE_STRUCTURE_INPUT_ID,
    LINEAGE_SYSTEM_STATE_LATEST_ID,
    METRIC_EGM_TASK_OBSERVATION_V1,
    OBSERVATION_ALPHA_Q0_FIRST_ID,
    OBSERVATION_ALPHA_Q0_SECOND_ID,
    QUBIT_ALPHA_INDEX0_ID,
    SCOPE_ALPHA_LEFT_PAIR_ID,
    SEED_SOURCE_ID,
    STRUCTURE_SNAPSHOT_ALPHA_LATEST_ID,
    STRUCTURE_SNAPSHOT_ALPHA_SUPERSEDED_ID,
    STRUCTURE_EVENT_ALPHA_COMPONENT_ADDED_ID,
    STRUCTURE_EVENT_ALPHA_TOPOLOGY_ID,
    SYSTEM_STATE_ALPHA_LATEST_ID,
    SYSTEM_STATE_ALPHA_SUPERSEDED_ID,
)


def main() -> int:
    dsn = os.environ.get("EGM_PG_DSN")
    if not dsn:
        print("EGM_PG_DSN not set; skip run_p0_queries", file=sys.stderr)
        return 0
    try:
        from psycopg import Connection
        from psycopg.rows import dict_row
    except ImportError:
        print("psycopg not installed; skip run_p0_queries", file=sys.stderr)
        return 0

    root = Path(__file__).resolve().parents[2]
    p0 = root / "sql" / "queries" / "p0"
    files: list[tuple[str, Path, dict[str, object]]] = [
        ("q01", p0 / "q01_chip_by_id.sql", {"chip_id": CHIP_ALPHA_ID}),
        ("q02", p0 / "q02_list_chip_qubits.sql", {"chip_id": CHIP_ALPHA_ID}),
        ("q03", p0 / "q03_list_chip_couplers.sql", {"chip_id": CHIP_ALPHA_ID}),
        ("q04", p0 / "q04_list_object_scopes.sql", {"chip_id": CHIP_ALPHA_ID}),
        ("q05", p0 / "q05_structure_snapshot_latest.sql", {"chip_id": CHIP_ALPHA_ID}),
        (
            "q06_mid",
            p0 / "q06_structure_snapshot_as_effective_at.sql",
            {"chip_id": CHIP_ALPHA_ID, "t": "2026-04-10T12:00:00Z"},
        ),
        (
            "q06_late",
            p0 / "q06_structure_snapshot_as_effective_at.sql",
            {"chip_id": CHIP_ALPHA_ID, "t": "2026-04-20T12:00:00Z"},
        ),
        ("q07", p0 / "q07_structure_events_by_chip.sql", {"chip_id": CHIP_ALPHA_ID}),
        (
            "q07_p0",
            p0 / "q07_structure_events_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "t_start": None,
                "t_end": None,
                "limit": 1,
                "offset": 0,
            },
        ),
        (
            "q07_p1",
            p0 / "q07_structure_events_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "t_start": None,
                "t_end": None,
                "limit": 1,
                "offset": 1,
            },
        ),
        (
            "q07_win",
            p0 / "q07_structure_events_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "t_start": "2026-04-01T00:00:00Z",
                "t_end": "2026-04-10T00:00:00Z",
                "limit": 10,
                "offset": 0,
            },
        ),
        ("q08", p0 / "q08_calibration_runs_by_chip.sql", {"chip_id": CHIP_ALPHA_ID}),
        (
            "q08_p0",
            p0 / "q08_calibration_runs_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "t_start": None,
                "t_end": None,
                "target_scope_id": None,
                "limit": 1,
                "offset": 0,
            },
        ),
        (
            "q08_p1",
            p0 / "q08_calibration_runs_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "t_start": None,
                "t_end": None,
                "target_scope_id": None,
                "limit": 1,
                "offset": 1,
            },
        ),
        (
            "q08_scope",
            p0 / "q08_calibration_runs_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "t_start": None,
                "t_end": None,
                "target_scope_id": SCOPE_ALPHA_LEFT_PAIR_ID,
                "limit": 10,
                "offset": 0,
            },
        ),
        (
            "q08_win",
            p0 / "q08_calibration_runs_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "t_start": "2026-05-01T00:00:00Z",
                "t_end": "2026-05-04T00:00:00Z",
                "target_scope_id": None,
                "limit": 10,
                "offset": 0,
            },
        ),
        (
            "q09",
            p0 / "q09_calibration_artifacts_by_run.sql",
            {"calibration_run_id": CALIBRATION_RUN_ALPHA_READOUT_SEED_ID},
        ),
        ("q10", p0 / "q10_calibration_snapshot_latest.sql", {"chip_id": CHIP_ALPHA_ID}),
        (
            "q11_cal_mid",
            p0 / "q11_calibration_snapshot_as_effective_at.sql",
            {"chip_id": CHIP_ALPHA_ID, "t": "2026-05-05T12:00:00Z"},
        ),
        (
            "q11_cal_late",
            p0 / "q11_calibration_snapshot_as_effective_at.sql",
            {"chip_id": CHIP_ALPHA_ID, "t": "2026-05-15T12:00:00Z"},
        ),
        ("q12", p0 / "q12_benchmark_runs_by_chip.sql", {"chip_id": CHIP_ALPHA_ID}),
        (
            "q12_p0",
            p0 / "q12_benchmark_runs_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "bench_name": None,
                "t_start": None,
                "t_end": None,
                "target_scope_id": None,
                "limit": 1,
                "offset": 0,
            },
        ),
        (
            "q12_p1",
            p0 / "q12_benchmark_runs_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "bench_name": None,
                "t_start": None,
                "t_end": None,
                "target_scope_id": None,
                "limit": 1,
                "offset": 1,
            },
        ),
        (
            "q12_name",
            p0 / "q12_benchmark_runs_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "bench_name": "xeb-demo-seed",
                "t_start": None,
                "t_end": None,
                "target_scope_id": None,
                "limit": 10,
                "offset": 0,
            },
        ),
        (
            "q12_win",
            p0 / "q12_benchmark_runs_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "bench_name": None,
                "t_start": "2026-05-01T00:00:00Z",
                "t_end": "2026-05-04T00:00:00Z",
                "target_scope_id": None,
                "limit": 10,
                "offset": 0,
            },
        ),
        (
            "q13",
            p0 / "q13_observation_history_by_subject.sql",
            {
                "subject_id": QUBIT_ALPHA_INDEX0_ID,
                "metric_definition_id": METRIC_EGM_TASK_OBSERVATION_V1,
                "start": "2026-05-02T00:00:00Z",
                "end": "2026-05-03T00:00:00Z",
            },
        ),
        (
            "q14_p0",
            p0 / "q14_metric_history_paged.sql",
            {
                "subject_type": "qubit",
                "subject_id": QUBIT_ALPHA_INDEX0_ID,
                "metric_definition_id": METRIC_EGM_TASK_OBSERVATION_V1,
                "start": "2026-05-02T00:00:00Z",
                "end": "2026-05-04T00:00:00Z",
                "limit": 1,
                "offset": 0,
            },
        ),
        (
            "q14_p1",
            p0 / "q14_metric_history_paged.sql",
            {
                "subject_type": "qubit",
                "subject_id": QUBIT_ALPHA_INDEX0_ID,
                "metric_definition_id": METRIC_EGM_TASK_OBSERVATION_V1,
                "start": "2026-05-02T00:00:00Z",
                "end": "2026-05-04T00:00:00Z",
                "limit": 1,
                "offset": 1,
            },
        ),
        (
            "q14_all",
            p0 / "q14_metric_history_paged.sql",
            {
                "subject_type": "qubit",
                "subject_id": QUBIT_ALPHA_INDEX0_ID,
                "metric_definition_id": METRIC_EGM_TASK_OBSERVATION_V1,
                "start": "2026-05-02T00:00:00Z",
                "end": "2026-05-04T00:00:00Z",
                "limit": 20,
                "offset": 0,
            },
        ),
        (
            "q15",
            p0 / "q15_observation_producer_fields.sql",
            {"observation_record_id": OBSERVATION_ALPHA_Q0_FIRST_ID},
        ),
        ("q16", p0 / "q16_system_state_latest.sql", {"chip_id": CHIP_ALPHA_ID}),
        (
            "q17_st_mid",
            p0 / "q17_system_state_as_effective_at.sql",
            {"chip_id": CHIP_ALPHA_ID, "t": "2026-05-05T12:00:00Z"},
        ),
        (
            "q17_st_late",
            p0 / "q17_system_state_as_effective_at.sql",
            {"chip_id": CHIP_ALPHA_ID, "t": "2026-05-12T12:00:00Z"},
        ),
        (
            "q18_known_mid",
            p0 / "q18_system_state_as_known_at.sql",
            {"chip_id": CHIP_ALPHA_ID, "t": "2026-05-06T12:00:00Z"},
        ),
        (
            "q18_known_late",
            p0 / "q18_system_state_as_known_at.sql",
            {"chip_id": CHIP_ALPHA_ID, "t": "2026-05-13T12:00:00Z"},
        ),
        ("q15_src", p0 / "q15_step2_source_by_id.sql", {"source_id": SEED_SOURCE_ID}),
        (
            "q19",
            p0 / "q19_lineage_by_downstream.sql",
            {
                "downstream_object_type": "system_state",
                "downstream_object_id": SYSTEM_STATE_ALPHA_LATEST_ID,
            },
        ),
        ("q20", p0 / "q20_lineage_edges_by_lineage_id.sql", {"lineage_id": LINEAGE_SYSTEM_STATE_LATEST_ID}),
        ("q22", p0 / "q22_recent_ingested_facts.sql", {"chip_id": CHIP_ALPHA_ID}),
        (
            "q23_both",
            p0 / "q23_known_observations.sql",
            {"chip_id": CHIP_ALPHA_ID, "t": "2026-05-03T15:00:00Z"},
        ),
        (
            "q23_one",
            p0 / "q23_known_observations.sql",
            {"chip_id": CHIP_ALPHA_ID, "t": "2026-05-02T20:00:00Z"},
        ),
        (
            "q22_f",
            p0 / "q22_recent_ingested_facts_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "start": None,
                "end": None,
                "limit": 5,
            },
        ),
        (
            "q22_win",
            p0 / "q22_recent_ingested_facts_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "start": "2026-05-02T00:00:00Z",
                "end": "2026-05-10T00:00:00Z",
                "limit": 20,
            },
        ),
        (
            "q23_f",
            p0 / "q23_known_observations_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "t": "2026-05-15T12:00:00Z",
                "subject_type": "qubit",
                "subject_id": QUBIT_ALPHA_INDEX0_ID,
                "metric_definition_id": METRIC_EGM_TASK_OBSERVATION_V1,
                "limit": 10,
                "offset": 0,
            },
        ),
        (
            "q23_off",
            p0 / "q23_known_observations_filtered.sql",
            {
                "chip_id": CHIP_ALPHA_ID,
                "t": "2026-05-15T12:00:00Z",
                "subject_type": "qubit",
                "subject_id": QUBIT_ALPHA_INDEX0_ID,
                "metric_definition_id": METRIC_EGM_TASK_OBSERVATION_V1,
                "limit": 10,
                "offset": 1,
            },
        ),
    ]

    with Connection.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            for label, path, params in files:
                sql = path.read_text()
                cur.execute(sql, params)
                rows = cur.fetchall()
                if not rows:
                    print(f"{label}: expected rows from {path.name}, got 0", file=sys.stderr)
                    return 1
                if label == "q01" and rows[0].get("chip_name") != "chip-alpha":
                    print(f"{label}: chip_name mismatch {rows[0]}", file=sys.stderr)
                    return 1
                if label == "q02" and len(rows) != 4:
                    print(f"{label}: expected 4 qubits, got {len(rows)}", file=sys.stderr)
                    return 1
                if label == "q03" and len(rows) != 3:
                    print(f"{label}: expected 3 couplers, got {len(rows)}", file=sys.stderr)
                    return 1
                if label == "q04" and len(rows) != 2:
                    print(f"{label}: expected 2 scopes, got {len(rows)}", file=sys.stderr)
                    return 1
                if label == "q05":
                    rid = str(rows[0].get("structure_snapshot_id"))
                    if rid != STRUCTURE_SNAPSHOT_ALPHA_LATEST_ID:
                        print(f"{label}: expected latest structure snapshot id, got {rid}", file=sys.stderr)
                        return 1
                if label == "q06_mid":
                    rid = str(rows[0].get("structure_snapshot_id"))
                    if rid != STRUCTURE_SNAPSHOT_ALPHA_SUPERSEDED_ID:
                        print(f"{label}: expected superseded structure snapshot, got {rid}", file=sys.stderr)
                        return 1
                if label == "q06_late":
                    rid = str(rows[0].get("structure_snapshot_id"))
                    if rid != STRUCTURE_SNAPSHOT_ALPHA_LATEST_ID:
                        print(f"{label}: expected latest structure snapshot, got {rid}", file=sys.stderr)
                        return 1
                if label == "q07" and len(rows) != 2:
                    print(f"{label}: expected 2 structure events, got {len(rows)}", file=sys.stderr)
                    return 1
                if label == "q07_p0":
                    if len(rows) != 1 or str(rows[0]["structure_event_id"]) != STRUCTURE_EVENT_ALPHA_COMPONENT_ADDED_ID:
                        print(f"{label}: expected newest structure event (component_added)", file=sys.stderr)
                        return 1
                if label == "q07_p1":
                    if len(rows) != 1 or str(rows[0]["structure_event_id"]) != STRUCTURE_EVENT_ALPHA_TOPOLOGY_ID:
                        print(f"{label}: expected older structure event (topology_changed)", file=sys.stderr)
                        return 1
                if label == "q07_win":
                    if len(rows) != 1 or str(rows[0]["structure_event_id"]) != STRUCTURE_EVENT_ALPHA_TOPOLOGY_ID:
                        print(f"{label}: expected topology event in Apr1..Apr10 event_time window", file=sys.stderr)
                        return 1
                if label == "q08":
                    if len(rows) != 2 or str(rows[0]["calibration_run_id"]) != CALIBRATION_RUN_ALPHA_GATE_SEED_ID:
                        print(f"{label}: expected 2 runs, newest gate_cal first", file=sys.stderr)
                        return 1
                if label == "q08_p0":
                    if len(rows) != 1 or str(rows[0]["calibration_run_id"]) != CALIBRATION_RUN_ALPHA_GATE_SEED_ID:
                        print(f"{label}: expected gate_cal (limit 1 offset 0)", file=sys.stderr)
                        return 1
                if label == "q08_p1":
                    if len(rows) != 1 or str(rows[0]["calibration_run_id"]) != CALIBRATION_RUN_ALPHA_READOUT_SEED_ID:
                        print(f"{label}: expected readout_cal (limit 1 offset 1)", file=sys.stderr)
                        return 1
                if label == "q08_scope":
                    if len(rows) != 1 or str(rows[0]["calibration_run_id"]) != CALIBRATION_RUN_ALPHA_READOUT_SEED_ID:
                        print(f"{label}: expected readout run for alpha-left-pair scope", file=sys.stderr)
                        return 1
                if label == "q08_win":
                    if len(rows) != 1 or str(rows[0]["calibration_run_id"]) != CALIBRATION_RUN_ALPHA_READOUT_SEED_ID:
                        print(f"{label}: expected readout_cal in May1..May4 start_time window", file=sys.stderr)
                        return 1
                if label == "q09":
                    if len(rows) != 1 or str(rows[0]["calibration_artifact_id"]) != CALIBRATION_ARTIFACT_READOUT_SEED_ID:
                        print(f"{label}: expected single readout artifact", file=sys.stderr)
                        return 1
                if label == "q10":
                    rid = str(rows[0].get("calibration_snapshot_id"))
                    if rid != CALIBRATION_SNAPSHOT_ALPHA_LATEST_ID:
                        print(f"{label}: expected latest calibration snapshot, got {rid}", file=sys.stderr)
                        return 1
                if label == "q11_cal_mid":
                    rid = str(rows[0].get("calibration_snapshot_id"))
                    if rid != CALIBRATION_SNAPSHOT_ALPHA_SUPERSEDED_ID:
                        print(f"{label}: expected superseded cal snapshot, got {rid}", file=sys.stderr)
                        return 1
                if label == "q11_cal_late":
                    rid = str(rows[0].get("calibration_snapshot_id"))
                    if rid != CALIBRATION_SNAPSHOT_ALPHA_LATEST_ID:
                        print(f"{label}: expected latest cal snapshot, got {rid}", file=sys.stderr)
                        return 1
                if label == "q12":
                    if len(rows) != 2:
                        print(f"{label}: expected 2 seeded benchmark runs, got {len(rows)}", file=sys.stderr)
                        return 1
                    names = {str(r.get("benchmark_name")) for r in rows}
                    if names != {"xeb-demo-seed", "rb-demo-seed"}:
                        print(f"{label}: expected xeb-demo-seed and rb-demo-seed, got {names}", file=sys.stderr)
                        return 1
                    if str(rows[0]["benchmark_run_id"]) != BENCHMARK_RUN_SEED_RB_LATEST_ID:
                        print(f"{label}: expected newest run first (rb-demo-seed)", file=sys.stderr)
                        return 1
                if label == "q12_p0":
                    if len(rows) != 1 or str(rows[0]["benchmark_run_id"]) != BENCHMARK_RUN_SEED_RB_LATEST_ID:
                        print(f"{label}: expected rb-demo-seed row (limit 1 offset 0)", file=sys.stderr)
                        return 1
                if label == "q12_p1":
                    if len(rows) != 1 or str(rows[0]["benchmark_run_id"]) != BENCHMARK_RUN_SEED_DEMO_ID:
                        print(f"{label}: expected xeb-demo-seed row (limit 1 offset 1)", file=sys.stderr)
                        return 1
                if label == "q12_name":
                    if len(rows) != 1 or str(rows[0]["benchmark_run_id"]) != BENCHMARK_RUN_SEED_DEMO_ID:
                        print(f"{label}: expected single xeb-demo-seed by name filter", file=sys.stderr)
                        return 1
                if label == "q12_win":
                    if len(rows) != 1 or str(rows[0]["benchmark_run_id"]) != BENCHMARK_RUN_SEED_DEMO_ID:
                        print(f"{label}: expected xeb in May1..May4 start_time window", file=sys.stderr)
                        return 1
                if label == "q13":
                    if len(rows) != 1 or str(rows[0]["observation_record_id"]) != OBSERVATION_ALPHA_Q0_FIRST_ID:
                        print(f"{label}: expected single observation in window", file=sys.stderr)
                        return 1
                if label == "q14_p0":
                    if len(rows) != 1 or str(rows[0]["observation_record_id"]) != OBSERVATION_ALPHA_Q0_FIRST_ID:
                        print(f"{label}: expected first observation (limit 1 offset 0)", file=sys.stderr)
                        return 1
                if label == "q14_p1":
                    if len(rows) != 1 or str(rows[0]["observation_record_id"]) != OBSERVATION_ALPHA_Q0_SECOND_ID:
                        print(f"{label}: expected second observation (limit 1 offset 1)", file=sys.stderr)
                        return 1
                if label == "q14_all":
                    if len(rows) != 2 or {str(r["observation_record_id"]) for r in rows} != {
                        OBSERVATION_ALPHA_Q0_FIRST_ID,
                        OBSERVATION_ALPHA_Q0_SECOND_ID,
                    }:
                        print(f"{label}: expected both seeded observations in window", file=sys.stderr)
                        return 1
                if label == "q15":
                    r0 = rows[0]
                    if str(r0.get("producer_id")) != BENCHMARK_RUN_SEED_DEMO_ID or str(
                        r0.get("producer_type")
                    ) != "benchmark_run":
                        print(f"{label}: producer mismatch {r0}", file=sys.stderr)
                        return 1
                if label == "q16":
                    rid = str(rows[0].get("system_state_id"))
                    if rid != SYSTEM_STATE_ALPHA_LATEST_ID:
                        print(f"{label}: expected latest system_state, got {rid}", file=sys.stderr)
                        return 1
                if label == "q17_st_mid":
                    rid = str(rows[0].get("system_state_id"))
                    if rid != SYSTEM_STATE_ALPHA_SUPERSEDED_ID:
                        print(f"{label}: expected superseded system_state, got {rid}", file=sys.stderr)
                        return 1
                if label == "q17_st_late":
                    rid = str(rows[0].get("system_state_id"))
                    if rid != SYSTEM_STATE_ALPHA_LATEST_ID:
                        print(f"{label}: expected latest system_state at t, got {rid}", file=sys.stderr)
                        return 1
                if label == "q18_known_mid":
                    rid = str(rows[0].get("system_state_id"))
                    if rid != SYSTEM_STATE_ALPHA_SUPERSEDED_ID:
                        print(f"{label}: as_known_at mid expected superseded state", file=sys.stderr)
                        return 1
                if label == "q18_known_late":
                    rid = str(rows[0].get("system_state_id"))
                    if rid != SYSTEM_STATE_ALPHA_LATEST_ID:
                        print(f"{label}: as_known_at late expected latest state", file=sys.stderr)
                        return 1
                if label == "q15_src":
                    if rows[0].get("source_name") != "egm-phase1-seed":
                        print(f"{label}: unexpected source row {rows[0]}", file=sys.stderr)
                        return 1
                if label == "q19":
                    if len(rows) != 1 or str(rows[0].get("lineage_id")) != LINEAGE_SYSTEM_STATE_LATEST_ID:
                        print(f"{label}: expected single lineage header", file=sys.stderr)
                        return 1
                if label == "q20":
                    if len(rows) != 2:
                        print(f"{label}: expected 2 lineage edges", file=sys.stderr)
                        return 1
                    eids = {str(r["lineage_edge_id"]) for r in rows}
                    if eids != {
                        LINEAGE_EDGE_STRUCTURE_INPUT_ID,
                        LINEAGE_EDGE_CALIBRATION_INPUT_ID,
                    }:
                        print(f"{label}: unexpected edge ids {eids}", file=sys.stderr)
                        return 1
                if label == "q22" and len(rows) < 6:
                    print(f"{label}: expected at least 6 union rows, got {len(rows)}", file=sys.stderr)
                    return 1
                if label == "q23_both":
                    if len(rows) != 2 or {str(r["observation_record_id"]) for r in rows} != {
                        OBSERVATION_ALPHA_Q0_FIRST_ID,
                        OBSERVATION_ALPHA_Q0_SECOND_ID,
                    }:
                        print(f"{label}: expected both seeded observations", file=sys.stderr)
                        return 1
                if label == "q23_one":
                    if len(rows) != 1 or str(rows[0]["observation_record_id"]) != OBSERVATION_ALPHA_Q0_FIRST_ID:
                        print(f"{label}: expected first observation only before second ingest", file=sys.stderr)
                        return 1
                if label == "q22_f" and len(rows) != 5:
                    print(f"{label}: expected limit 5 rows, got {len(rows)}", file=sys.stderr)
                    return 1
                if label == "q22_win" and len(rows) != 4:
                    print(f"{label}: expected 4 ingested rows in May2..May10 window", file=sys.stderr)
                    return 1
                if label == "q23_f":
                    if len(rows) != 2 or {str(r["observation_record_id"]) for r in rows} != {
                        OBSERVATION_ALPHA_Q0_FIRST_ID,
                        OBSERVATION_ALPHA_Q0_SECOND_ID,
                    }:
                        print(f"{label}: filtered known-obs mismatch", file=sys.stderr)
                        return 1
                if label == "q23_off":
                    if len(rows) != 1 or str(rows[0]["observation_record_id"]) != OBSERVATION_ALPHA_Q0_FIRST_ID:
                        print(f"{label}: offset 1 should return older-ingested observation", file=sys.stderr)
                        return 1
                print(f"{label}: ok ({len(rows)} row(s))")
    print("run_p0_queries: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
