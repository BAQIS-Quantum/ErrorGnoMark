#!/usr/bin/env python3
"""Assert minimal row counts after apply_phase1.sh (requires psycopg + EGM_PG_DSN)."""
from __future__ import annotations

import os
import sys


def main() -> int:
    dsn = os.environ.get("EGM_PG_DSN")
    if not dsn:
        print("EGM_PG_DSN not set; skip verify_seed_counts", file=sys.stderr)
        return 0
    try:
        from psycopg import Connection
        from psycopg.rows import dict_row
    except ImportError:
        print("psycopg not installed; skip verify_seed_counts", file=sys.stderr)
        return 0

    exact: list[tuple[str, int]] = [
        ("chip", 3),  # chip-alpha, chip-beta, Baihua (seed 050)
        ("qubit", 8),
        ("coupler", 6),
        ("scope", 5),  # seed 010 + 050 baihua-chip-scope
        ("source", 2),  # seed 010 + 050 quafu feed
        ("metric_definition", 6),  # seed 010 + 050 quafu metrics ×5
        ("structure_snapshot", 2),
        ("structure_event", 2),
        ("calibration_run", 2),
        ("calibration_artifact", 2),
        ("calibration_snapshot", 2),
        ("system_state", 2),
        ("lineage", 1),
        ("lineage_edge", 2),
    ]
    minimum: list[tuple[str, int]] = [
        ("benchmark_run", 2),
        ("observation_record", 2),
    ]
    with Connection.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            for table, expected in exact:
                cur.execute(f"SELECT count(*)::int AS c FROM {table}")
                n = cur.fetchone()["c"]
                if n != expected:
                    print(f"{table}: expected exactly {expected}, got {n}", file=sys.stderr)
                    return 1
            for table, expected_min in minimum:
                cur.execute(f"SELECT count(*)::int AS c FROM {table}")
                n = cur.fetchone()["c"]
                if n < expected_min:
                    print(f"{table}: expected at least {expected_min}, got {n}", file=sys.stderr)
                    return 1
    print("verify_seed_counts: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
