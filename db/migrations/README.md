# EGM schema migrations

Forward-only SQL migrations for PostgreSQL Phase 1. Target version: see [schema_version.txt](../schema_version.txt).

## Apply

After bootstrap (`apply_phase1.sh`) or on an existing Phase 1 database:

```bash
export EGM_PG_DSN='postgresql://USER:PASS@HOST:5432/DBNAME'
python scripts/postgres/apply_migrations.py
```

Fresh CI/dev: `apply_phase1.sh` runs migrations automatically at the end.

## Files

| Version | File | Description |
|---------|------|-------------|
| 0001 | `0001_baseline.sql` | `egm_schema_migration` registry |
| 0002 | `0002_record_kind.sql` | `record_kind` + forecast columns (`phase1_v1.1`) |

## Policy

See [../MIGRATION.md](../MIGRATION.md) for upgrade, rollback, and compatibility rules.
