# EGM Data Layer (Phase 1)

Phase 1 PostgreSQL stores **metric facts** (observations, inferences, forecasts), hardware structure, calibration runs, and lineage. This directory documents **semantics and schema contracts** for operators and contributors.

## Documents

| Document | Description |
|----------|-------------|
| [observation-inference-forecast.md](observation-inference-forecast.md) | **Observation / Inference / Forecast** — definitions, write rules, anti-patterns |
| [observation-schema.md](observation-schema.md) | `observation_record` field dictionary and Python store mapping |
| [query-catalog.md](query-catalog.md) | Static SQL templates under `sql/queries/p0/` |

## Related paths

| Path | Role |
|------|------|
| [db/phase1/](../../db/phase1/) | Bootstrap DDL and demo seed |
| [db/migrations/](../../db/migrations/) | Forward schema migrations (Horizon E) |
| [db/MIGRATION.md](../../db/MIGRATION.md) | Upgrade and version policy |
| [scripts/postgres/](../../scripts/postgres/) | `apply_phase1.sh`, `apply_migrations.py`, acceptance |
| [docs/performance/](../performance/) | PostgreSQL benchmark reports |

## Schema versions

| Version | Description |
|---------|-------------|
| `phase1_v1.0` | `001_schema.sql` + seed (no `record_kind`) |
| `phase1_v1.1` | Migration `0002` — `record_kind` + forecast metadata columns |

Fresh installs: run `apply_phase1.sh` (applies bootstrap + seed + migrations).

## Status

| Capability | Status |
|------------|--------|
| Phase 1 DDL + P0 queries | **Beta** |
| `record_kind` (O/I/F) | **Beta** (schema v1.1) |
| Forecasting runtime (`intelligence/forecasting`) | **Planned** — DB rows may exist; compute pipeline not shipped |
