# EGM static SQL queries

## Layout

| Directory | Schema version | Description |
|-----------|----------------|-------------|
| [p0/](p0/) | `phase1_v1.1` | Phase 1 demo and API-aligned templates (Q1–Q26) |

## Run

```bash
export EGM_PG_DSN='postgresql://...'
PYTHONPATH=src python scripts/postgres/run_p0_queries.py
```

CI: `python -m egm.datastore.phase1_acceptance --strict` after `apply_phase1.sh`.

## Version notes

- **phase1_v1.0:** `001_schema.sql` only (no `record_kind`).
- **phase1_v1.1:** migration `0002` adds `record_kind` on `observation_record`; seed rows default to `observation`.

See [docs/data-layer/query-catalog.md](../docs/data-layer/query-catalog.md) for the query map.
