# PostgreSQL performance reports

Lab-scale benchmarks for Phase 1. EGM does **not** claim web-scale or multi-tenant production limits here.

## Reproduce

```bash
export EGM_PG_DSN='postgresql://postgres:postgres@localhost:5432/egm_bench'
createdb egm_bench  # once
./scripts/postgres/apply_phase1.sh

PYTHONPATH=src python scripts/benchmark/phase1_insert_benchmark.py --count 100000
PYTHONPATH=src python scripts/benchmark/phase1_query_benchmark.py --iterations 50
```

See [scripts/benchmark/README.md](../../scripts/benchmark/README.md).

## Reports

| Report | Description |
|--------|-------------|
| [postgres-benchmark-v0.1.md](postgres-benchmark-v0.1.md) | First baseline (insert + query latency) |

Refresh numbers after hardware or schema changes; note environment in each report.
