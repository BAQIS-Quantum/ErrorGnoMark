# PostgreSQL benchmark v0.1 (Phase 1)

**Date:** 2026-05-16  
**Schema:** `phase1_v1.1` (migration `0002`, `record_kind` on `observation_record`)  
**EGM:** workspace `main` + Horizon E (unreleased)

## Environment

| Item | Value |
|------|--------|
| PostgreSQL | 15.x (local Homebrew, macOS) |
| Client | `psycopg` 3.x, Python 3.12 |
| Dataset | Phase 1 seed + **100,000** synthetic `observation_record` rows (`chip-alpha`) |
| Hardware | Developer laptop (not CI); numbers are indicative |

Reproduce: [README.md](README.md).

## Insert throughput

| Test | Rows | Elapsed | Throughput |
|------|------|---------|------------|
| Bulk `INSERT` (`executemany`, batch 2000) | 100,000 | 4.86 s | **~20,600 rows/s** |

Script: `scripts/benchmark/phase1_insert_benchmark.py`.

**Notes:** Single connection, no parallelism, no `COPY`. Production ingest may use batch ETL or `COPY` for higher throughput.

## Query latency (30 iterations, warm cache)

After bulk insert, `observation_record` ≈ 100k+ rows on `chip-alpha`.

| Query | p50 | p95 | Template |
|-------|-----|-----|----------|
| Q13 observation history | 0.56 ms | 164 ms | `q13_observation_history_by_subject.sql` |
| Q22 recent ingested facts | 45.6 ms | 127 ms | `q22_recent_ingested_facts.sql` |
| Q19 lineage by downstream | 0.11 ms | 0.83 ms | `q19_lineage_by_downstream.sql` |
| Q17 system state as-of | 0.14 ms | 1.35 ms | `q17_system_state_as_effective_at.sql` |

Script: `scripts/benchmark/phase1_query_benchmark.py --iterations 30`.

**Notes:** Q22 scans recent ingested rows chip-wide; cost grows with table size. Q13 p95 variance likely from first-query planning on a large table. Seed-only DB (no bulk insert) is much faster for Q22.

## P0 acceptance

`python -m egm.datastore.phase1_acceptance --strict` — row counts + Q1–Q23 on **seed-only** database (CI uses fresh Postgres 15 service).

## Limits (not tested in v0.1)

| Topic | Status |
|-------|--------|
| 1M row insert | Not run |
| Concurrent writers | Not tested |
| Lineage depth > 2 hops | Seed has depth 2 |
| Partitioning / RLS | Not implemented |
| Multi-tenant isolation | Not implemented |

## Interpretation

Phase 1 targets **team / lab-scale** workloads: thousands to low millions of facts per chip with indexed temporal queries. Web-scale or sub-millisecond SLAs are out of scope. Refresh this report after schema or hardware changes.
