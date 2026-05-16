#!/usr/bin/env python3
"""
Time representative Phase 1 P0 queries (latency p50/p95 over iterations).

Requires EGM_PG_DSN, schema + seed + migrations, psycopg.

Example:
  PYTHONPATH=src python scripts/benchmark/phase1_query_benchmark.py --iterations 50
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from pathlib import Path


def _percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def _bench(cur, name: str, sql: str, params: dict, iterations: int) -> dict[str, float]:
    samples: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        cur.execute(sql, params)
        cur.fetchall()
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    return {
        "name": name,
        "p50_ms": statistics.median(samples),
        "p95_ms": _percentile(samples, 0.95),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=30)
    args = parser.parse_args()

    dsn = os.environ.get("EGM_PG_DSN")
    if not dsn:
        print("EGM_PG_DSN is not set", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))

    from egm.datastore.phase1_pg_constants import (
        CHIP_ALPHA_ID,
        METRIC_EGM_TASK_OBSERVATION_V1,
        QUBIT_ALPHA_INDEX0_ID,
        SYSTEM_STATE_ALPHA_LATEST_ID,
    )

    try:
        from psycopg import Connection
        from psycopg.rows import dict_row
    except ImportError:
        print("psycopg required", file=sys.stderr)
        return 1

    p0 = root / "sql" / "queries" / "p0"
    queries: list[tuple[str, Path, dict]] = [
        (
            "Q13_observation_history",
            p0 / "q13_observation_history_by_subject.sql",
            {
                "subject_id": QUBIT_ALPHA_INDEX0_ID,
                "metric_definition_id": METRIC_EGM_TASK_OBSERVATION_V1,
                "start": "2026-05-02T00:00:00Z",
                "end": "2026-05-04T00:00:00Z",
            },
        ),
        ("Q22_recent_ingested", p0 / "q22_recent_ingested_facts.sql", {"chip_id": CHIP_ALPHA_ID}),
        (
            "Q19_lineage",
            p0 / "q19_lineage_by_downstream.sql",
            {
                "downstream_object_type": "system_state",
                "downstream_object_id": SYSTEM_STATE_ALPHA_LATEST_ID,
            },
        ),
        (
            "Q17_system_state_as_of",
            p0 / "q17_system_state_as_effective_at.sql",
            {"chip_id": CHIP_ALPHA_ID, "t": "2026-05-12T12:00:00Z"},
        ),
    ]

    results: list[dict[str, float | str]] = []
    with Connection.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            for name, path, params in queries:
                if not path.is_file():
                    print(f"missing {path}", file=sys.stderr)
                    return 1
                sql = path.read_text(encoding="utf-8")
                row = _bench(cur, name, sql, params, args.iterations)
                results.append(row)
                print(f"{name}: p50={row['p50_ms']:.2f}ms p95={row['p95_ms']:.2f}ms")

    print("\nJSON summary:")
    import json

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
