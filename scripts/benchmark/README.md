# Phase 1 PostgreSQL benchmarks

Requires `EGM_PG_DSN`, Phase 1 bootstrap + migrations, and `psycopg`.

```bash
export EGM_PG_DSN='postgresql://postgres:postgres@localhost:5432/egm_phase1'
./scripts/postgres/apply_phase1.sh

# Insert throughput (default 100k rows)
PYTHONPATH=src python scripts/benchmark/phase1_insert_benchmark.py

# Query latency (P0 subset)
PYTHONPATH=src python scripts/benchmark/phase1_query_benchmark.py --iterations 50
```

Results are recorded in [docs/performance/postgres-benchmark-v0.1.md](../../docs/performance/postgres-benchmark-v0.1.md).
