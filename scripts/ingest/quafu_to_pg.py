"""
Idempotent ETL: parsed Quafu calibration data → Phase 1 Postgres tables.

Writes (in a single transaction):
    1. UPSERT qubit × 156
    2. UPSERT coupler × 182 + coupler_endpoint × 364
    3. INSERT calibration_run × 1 (idempotent check by chip+time+run_type)
    4. INSERT calibration_artifact × 2 (full JSON + SVG ref)
    5. INSERT observation_record × ~806 (qubit metrics + coupler CZ fidelity)

Requires:
    - ``psycopg[binary]>=3.2``
    - ``db/phase1/seed/050_quafu_baihua_bootstrap.sql`` already applied
      (chip 'Baihua', source, 5 metric_definitions must exist)

Usage::

    python scripts/ingest/quafu_to_pg.py <csv_path> [--svg <svg_path>]

    # or from Python:
    from scripts.ingest.quafu_to_pg import ingest_quafu_calibration
    ingest_quafu_calibration(dsn, data, svg_ref="fixtures/quafu/...")
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from datetime import timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Quafu timestamps are in China Standard Time (UTC+8)
_CST = timezone(timedelta(hours=8))

logger = logging.getLogger(__name__)

# Append project root so constants are importable when run as script
_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.egm.datastore.phase1_pg_constants import (
    CHIP_BAIHUA_ID,
    METRIC_QUAFU_CZ_FIDELITY_ID,
    METRIC_QUAFU_FREQUENCY_ID,
    METRIC_QUAFU_SQ_FIDELITY_ID,
    METRIC_QUAFU_T1_ID,
    METRIC_QUAFU_T2_ID,
    SOURCE_QUAFU_BAIHUA_ID,
)
from scripts.ingest.quafu_csv_parser import (
    CouplerCalibration,
    QuafuCalibrationData,
    QubitCalibration,
    parse_quafu_csv,
)

try:
    from psycopg import Connection
    from psycopg.rows import dict_row
    from psycopg.types.json import Json
except ImportError:
    raise ImportError(
        "quafu_to_pg requires 'psycopg'. Install: pip install 'psycopg[binary]>=3.2'"
    )


def _uuid() -> str:
    return str(uuid.uuid4())


def _ensure_chip(cur: Any, chip_name: str) -> str:
    """Return chip_id for the given chip_name; raise if not seeded."""
    cur.execute(
        "SELECT chip_id::text FROM chip WHERE chip_name = %(n)s",
        {"n": chip_name},
    )
    row = cur.fetchone()
    if row is None:
        raise ValueError(
            f"Chip '{chip_name}' not found. "
            "Run: psql $EGM_PG_DSN -f db/phase1/seed/050_quafu_baihua_bootstrap.sql"
        )
    return row["chip_id"]


def _ensure_source(cur: Any) -> str:
    """Return source_id for quafu_baihua_calibration."""
    cur.execute(
        "SELECT source_id::text FROM source WHERE source_id = %(sid)s::uuid",
        {"sid": SOURCE_QUAFU_BAIHUA_ID},
    )
    row = cur.fetchone()
    if row is None:
        raise ValueError(
            "Source 'quafu_baihua_calibration' not found. Apply seed 050 first."
        )
    return row["source_id"]


def _check_already_ingested(cur: Any, chip_id: str, cal_time_iso: str) -> bool:
    """Return True if this calibration run already exists (idempotent guard)."""
    cur.execute(
        """
        SELECT 1 FROM calibration_run
        WHERE chip_id = %(cid)s::uuid
          AND run_type = 'quafu_full_chip_calibration'
          AND start_time = %(st)s::timestamptz
        LIMIT 1
        """,
        {"cid": chip_id, "st": cal_time_iso},
    )
    return cur.fetchone() is not None


def _upsert_qubits(
    cur: Any, chip_id: str, qubits: List[QubitCalibration]
) -> Dict[int, str]:
    """
    UPSERT qubit rows; return {qubit_index: qubit_id} mapping.
    """
    mapping: Dict[int, str] = {}
    for q in qubits:
        qid = _uuid()
        cur.execute(
            """
            INSERT INTO qubit (qubit_id, chip_id, qubit_index, qubit_label)
            VALUES (%(qid)s::uuid, %(cid)s::uuid, %(idx)s, %(lbl)s)
            ON CONFLICT (chip_id, qubit_index) DO NOTHING
            RETURNING qubit_id::text
            """,
            {
                "qid": qid,
                "cid": chip_id,
                "idx": q.qubit_index,
                "lbl": f"Q{q.qubit_index}",
            },
        )
        row = cur.fetchone()
        if row is not None:
            mapping[q.qubit_index] = row["qubit_id"]
        else:
            cur.execute(
                "SELECT qubit_id::text FROM qubit "
                "WHERE chip_id = %(cid)s::uuid AND qubit_index = %(idx)s",
                {"cid": chip_id, "idx": q.qubit_index},
            )
            mapping[q.qubit_index] = cur.fetchone()["qubit_id"]
    return mapping


def _upsert_couplers(
    cur: Any,
    chip_id: str,
    couplers: List[CouplerCalibration],
    qubit_map: Dict[int, str],
) -> Dict[Tuple[int, int], str]:
    """
    UPSERT coupler + coupler_endpoint rows; return {(a,b): coupler_id}.
    """
    mapping: Dict[Tuple[int, int], str] = {}

    for c in couplers:
        cname = f"CZ_{c.qubit_a}_{c.qubit_b}"
        cid = _uuid()

        cur.execute(
            """
            INSERT INTO coupler (coupler_id, chip_id, coupler_name, coupler_type, metadata_json)
            VALUES (%(cid)s::uuid, %(chip)s::uuid, %(name)s, 'cz', '{}'::jsonb)
            ON CONFLICT DO NOTHING
            RETURNING coupler_id::text
            """,
            {"cid": cid, "chip": chip_id, "name": cname},
        )
        row = cur.fetchone()
        if row is not None:
            coupler_id = row["coupler_id"]
        else:
            cur.execute(
                "SELECT coupler_id::text FROM coupler "
                "WHERE chip_id = %(chip)s::uuid AND coupler_name = %(name)s",
                {"chip": chip_id, "name": cname},
            )
            fetched = cur.fetchone()
            if fetched is None:
                raise ValueError(f"Failed to upsert coupler {cname}")
            coupler_id = fetched["coupler_id"]

        mapping[(c.qubit_a, c.qubit_b)] = coupler_id

        qa_id = qubit_map[c.qubit_a]
        qb_id = qubit_map[c.qubit_b]
        for order, qid in [(0, qa_id), (1, qb_id)]:
            cur.execute(
                """
                INSERT INTO coupler_endpoint
                    (coupler_endpoint_id, coupler_id, qubit_id, endpoint_order)
                VALUES (%(eid)s::uuid, %(cid)s::uuid, %(qid)s::uuid, %(ord)s)
                ON CONFLICT (coupler_id, qubit_id) DO NOTHING
                """,
                {"eid": _uuid(), "cid": coupler_id, "qid": qid, "ord": order},
            )

    return mapping


def _insert_calibration_run(
    cur: Any,
    chip_id: str,
    source_id: str,
    data: QuafuCalibrationData,
) -> str:
    """Insert calibration_run; return calibration_run_id."""
    run_id = _uuid()
    cal_time = data.calibration_time.replace(tzinfo=_CST)

    cur.execute(
        """
        INSERT INTO calibration_run (
            calibration_run_id, chip_id, run_type, target_scope_id,
            status, start_time, end_time, published_at, ingested_at,
            source_id, raw_payload_ref, payload_json
        ) VALUES (
            %(rid)s::uuid, %(cid)s::uuid, 'quafu_full_chip_calibration', NULL,
            'succeeded'::run_status_enum, %(st)s, %(st)s, %(st)s, now(),
            %(sid)s::uuid, %(csv)s, %(pj)s
        )
        RETURNING calibration_run_id::text
        """,
        {
            "rid": run_id,
            "cid": chip_id,
            "st": cal_time.isoformat(),
            "sid": source_id,
            "csv": data.csv_filename,
            "pj": Json(data.summary()),
        },
    )
    return cur.fetchone()["calibration_run_id"]


def _insert_artifacts(
    cur: Any,
    chip_id: str,
    source_id: str,
    run_id: str,
    data: QuafuCalibrationData,
    svg_ref: Optional[str],
) -> str:
    """Insert calibration_artifacts; return the main (parameter) artifact_id."""
    cal_time = data.calibration_time.replace(tzinfo=_CST)

    full_payload = {
        "qubits": [
            {
                "qubit_index": q.qubit_index,
                "t1_us": q.t1_us,
                "t2_us": q.t2_us,
                "frequency_ghz": q.frequency_ghz,
                "single_qubit_fidelity": q.single_qubit_fidelity,
            }
            for q in data.qubits
        ],
        "couplers": [
            {
                "qubit_a": c.qubit_a,
                "qubit_b": c.qubit_b,
                "cz_fidelity": c.cz_fidelity,
            }
            for c in data.couplers
        ],
        "summary": data.summary(),
    }

    main_artifact_id = _uuid()
    cur.execute(
        """
        INSERT INTO calibration_artifact (
            calibration_artifact_id, calibration_run_id, chip_id,
            artifact_type, artifact_schema_name, target_scope_id,
            produced_at, published_at, ingested_at,
            effective_from, effective_to,
            payload_json, payload_ref, source_id
        ) VALUES (
            %(aid)s::uuid, %(rid)s::uuid, %(cid)s::uuid,
            'calibration_parameter'::artifact_type_enum, 'quafu_full_chip_v1', NULL,
            %(pt)s, %(pt)s, now(),
            %(pt)s, NULL,
            %(pj)s, NULL, %(sid)s::uuid
        )
        """,
        {
            "aid": main_artifact_id,
            "rid": run_id,
            "cid": chip_id,
            "pt": cal_time.isoformat(),
            "pj": Json(full_payload),
            "sid": source_id,
        },
    )

    if svg_ref:
        cur.execute(
            """
            INSERT INTO calibration_artifact (
                calibration_artifact_id, calibration_run_id, chip_id,
                artifact_type, artifact_schema_name, target_scope_id,
                produced_at, published_at, ingested_at,
                effective_from, effective_to,
                payload_json, payload_ref, source_id
            ) VALUES (
                %(aid)s::uuid, %(rid)s::uuid, %(cid)s::uuid,
                'report'::artifact_type_enum, 'quafu_topology_svg', NULL,
                %(pt)s, %(pt)s, now(),
                %(pt)s, NULL,
                '{}'::jsonb, %(ref)s, %(sid)s::uuid
            )
            """,
            {
                "aid": _uuid(),
                "rid": run_id,
                "cid": chip_id,
                "pt": cal_time.isoformat(),
                "ref": svg_ref,
                "sid": source_id,
            },
        )

    return main_artifact_id


def _insert_observations(
    cur: Any,
    chip_id: str,
    source_id: str,
    artifact_id: str,
    data: QuafuCalibrationData,
    qubit_map: Dict[int, str],
    coupler_map: Dict[Tuple[int, int], str],
) -> int:
    """Insert observation_record rows. Returns count of rows inserted."""
    cal_time = data.calibration_time.replace(tzinfo=_CST)
    cal_iso = cal_time.isoformat()
    count = 0

    qubit_metrics = [
        (METRIC_QUAFU_T1_ID, lambda q: q.t1_us),
        (METRIC_QUAFU_T2_ID, lambda q: q.t2_us),
        (METRIC_QUAFU_FREQUENCY_ID, lambda q: q.frequency_ghz),
        (METRIC_QUAFU_SQ_FIDELITY_ID, lambda q: q.single_qubit_fidelity),
    ]

    for q in data.qubits:
        qid = qubit_map[q.qubit_index]
        for metric_id, value_fn in qubit_metrics:
            val = value_fn(q)
            flag = "suspect" if val == 0 else "validated"
            cur.execute(
                """
                INSERT INTO observation_record (
                    observation_record_id, chip_id,
                    subject_type, subject_id, scope_id,
                    metric_definition_id, producer_type, producer_id,
                    value_numeric, value_text, value_json, unit,
                    quality_flag, observation_time,
                    effective_from, effective_to, published_at, ingested_at,
                    source_id
                ) VALUES (
                    %(oid)s::uuid, %(cid)s::uuid,
                    'qubit'::subject_type_enum, %(sid)s::uuid, NULL,
                    %(mid)s::uuid, 'calibration_artifact'::producer_type_enum, %(pid)s::uuid,
                    %(val)s, NULL, NULL, NULL,
                    %(qf)s::quality_flag_enum, %(ot)s,
                    %(ot)s, NULL, %(ot)s, now(),
                    %(src)s::uuid
                )
                """,
                {
                    "oid": _uuid(),
                    "cid": chip_id,
                    "sid": qid,
                    "mid": metric_id,
                    "pid": artifact_id,
                    "val": val,
                    "qf": flag,
                    "ot": cal_iso,
                    "src": source_id,
                },
            )
            count += 1

    for c in data.couplers:
        cid = coupler_map[(c.qubit_a, c.qubit_b)]
        flag = "suspect" if c.cz_fidelity == 0 else "validated"
        cur.execute(
            """
            INSERT INTO observation_record (
                observation_record_id, chip_id,
                subject_type, subject_id, scope_id,
                metric_definition_id, producer_type, producer_id,
                value_numeric, value_text, value_json, unit,
                quality_flag, observation_time,
                effective_from, effective_to, published_at, ingested_at,
                source_id
            ) VALUES (
                %(oid)s::uuid, %(cid)s::uuid,
                'coupler'::subject_type_enum, %(sid)s::uuid, NULL,
                %(mid)s::uuid, 'calibration_artifact'::producer_type_enum, %(pid)s::uuid,
                %(val)s, NULL, NULL, NULL,
                %(qf)s::quality_flag_enum, %(ot)s,
                %(ot)s, NULL, %(ot)s, now(),
                %(src)s::uuid
            )
            """,
            {
                "oid": _uuid(),
                "cid": chip_id,
                "sid": cid,
                "mid": METRIC_QUAFU_CZ_FIDELITY_ID,
                "pid": artifact_id,
                "val": c.cz_fidelity,
                "qf": flag,
                "ot": cal_iso,
                "src": source_id,
            },
        )
        count += 1

    return count


# ── main entry point ──────────────────────────────────────────────────────────

def ingest_quafu_calibration(
    dsn: str,
    data: QuafuCalibrationData,
    svg_ref: Optional[str] = None,
) -> bool:
    """
    Ingest one Quafu calibration CSV into Phase 1 tables.

    Returns True if data was ingested, False if already present (idempotent skip).
    """
    cal_time = data.calibration_time.replace(tzinfo=_CST)

    with Connection.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            chip_id = _ensure_chip(cur, data.chip_name)
            source_id = _ensure_source(cur)

            if _check_already_ingested(cur, chip_id, cal_time.isoformat()):
                logger.info(
                    "Calibration %s already ingested for %s — skipping.",
                    cal_time.isoformat(), data.chip_name,
                )
                return False

            logger.info(
                "Ingesting %s calibration %s: %d qubits, %d couplers",
                data.chip_name, cal_time.isoformat(),
                data.num_qubits, data.num_couplers,
            )

            qubit_map = _upsert_qubits(cur, chip_id, data.qubits)
            coupler_map = _upsert_couplers(cur, chip_id, data.couplers, qubit_map)

            run_id = _insert_calibration_run(cur, chip_id, source_id, data)
            artifact_id = _insert_artifacts(
                cur, chip_id, source_id, run_id, data, svg_ref
            )
            obs_count = _insert_observations(
                cur, chip_id, source_id, artifact_id,
                data, qubit_map, coupler_map,
            )

        conn.commit()

    logger.info(
        "Ingested: 1 calibration_run, 2 artifacts, %d observation_records.", obs_count
    )
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Ingest a Quafu calibration CSV into Phase 1 Postgres."
    )
    parser.add_argument("csv_path", help="Path to the Quafu calibration CSV file")
    parser.add_argument("--svg", default=None, help="Relative path to SVG file (for artifact ref)")
    parser.add_argument(
        "--dsn",
        default=os.environ.get("EGM_PG_DSN", ""),
        help="Postgres DSN (default: $EGM_PG_DSN)",
    )
    args = parser.parse_args()

    if not args.dsn:
        print("ERROR: Set EGM_PG_DSN or pass --dsn", file=sys.stderr)
        sys.exit(1)

    data = parse_quafu_csv(args.csv_path)
    print(f"Parsed: {data.chip_name} @ {data.calibration_time.isoformat()}")
    print(f"  Qubits:   {data.num_qubits}")
    print(f"  Couplers: {data.num_couplers}")

    ingested = ingest_quafu_calibration(args.dsn, data, svg_ref=args.svg)
    if ingested:
        print("Ingest complete.")
    else:
        print("Already ingested — skipped.")


if __name__ == "__main__":
    main()
