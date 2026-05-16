#!/usr/bin/env python3
"""
Bulk-insert synthetic observation_record rows for throughput measurement.

Requires EGM_PG_DSN and Phase 1 schema + migrations (record_kind column).

Example:
  export EGM_PG_DSN=postgresql://postgres:postgres@localhost:5432/egm_bench
  python scripts/benchmark/phase1_insert_benchmark.py --count 100000 --batch-size 2000
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "src"))

from egm.datastore.phase1_pg_constants import (
    BENCHMARK_RUN_SEED_DEMO_ID,
    CHIP_ALPHA_ID,
    METRIC_EGM_TASK_OBSERVATION_V1,
    SEED_SOURCE_ID,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 observation_record insert benchmark")
    parser.add_argument("--count", type=int, default=100_000, help="Rows to insert")
    parser.add_argument("--batch-size", type=int, default=2_000, help="Rows per transaction")
    args = parser.parse_args()

    dsn = os.environ.get("EGM_PG_DSN")
    if not dsn:
        print("EGM_PG_DSN is not set", file=sys.stderr)
        return 1

    try:
        from psycopg import Connection
        from psycopg.types.json import Json
    except ImportError:
        print("psycopg required", file=sys.stderr)
        return 1

    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    insert_sql = """
        INSERT INTO observation_record (
            chip_id, subject_type, subject_id, metric_definition_id,
            producer_type, producer_id, value_numeric, value_json,
            quality_flag, observation_time, ingested_at, source_id, record_kind
        ) VALUES (
            %(chip_id)s::uuid, 'chip'::subject_type_enum, %(subject_id)s::uuid,
            %(metric_id)s::uuid, 'benchmark_run'::producer_type_enum,
            %(producer_id)s::uuid, %(value_numeric)s,
            %(value_json)s, 'raw'::quality_flag_enum, %(observation_time)s,
            now(), %(source_id)s::uuid, 'observation'::record_kind_enum
        )
    """

    total = args.count
    batch = max(1, args.batch_size)
    inserted = 0
    t0 = time.perf_counter()

    with Connection.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'observation_record' AND column_name = 'record_kind'"
            )
            if cur.fetchone() is None:
                print("record_kind column missing; run apply_migrations.py first", file=sys.stderr)
                return 1

        while inserted < total:
            n = min(batch, total - inserted)
            rows = []
            for i in range(n):
                idx = inserted + i
                rows.append(
                    {
                        "chip_id": CHIP_ALPHA_ID,
                        "subject_id": CHIP_ALPHA_ID,
                        "metric_id": METRIC_EGM_TASK_OBSERVATION_V1,
                        "producer_id": BENCHMARK_RUN_SEED_DEMO_ID,
                        "value_numeric": 0.5 + (idx % 1000) * 1e-6,
                        "value_json": Json({"bench": True, "idx": idx}),
                        "observation_time": base_time + timedelta(seconds=idx),
                        "source_id": SEED_SOURCE_ID,
                    }
                )
            with conn.cursor() as cur:
                cur.executemany(insert_sql, rows)
            conn.commit()
            inserted += n
            if inserted % (batch * 5) == 0 or inserted == total:
                print(f"  inserted {inserted}/{total}")

    elapsed = time.perf_counter() - t0
    rps = total / elapsed if elapsed > 0 else 0.0
    print(f"Done: {total} rows in {elapsed:.2f}s ({rps:,.0f} rows/s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
