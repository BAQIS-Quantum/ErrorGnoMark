# EGM database assets

| Path | Purpose |
|------|---------|
| [phase1/](phase1/) | Phase 1 bootstrap DDL (`001_schema.sql`) and demo seed |
| [migrations/](migrations/) | Forward schema migrations (Horizon E) |
| [schema_version.txt](schema_version.txt) | Target migration version |
| [MIGRATION.md](MIGRATION.md) | Upgrade policy |

**Scripts:** [scripts/postgres/](../scripts/postgres/) — `apply_phase1.sh`, `apply_migrations.py`, acceptance.

**Docs:** [docs/data-layer/](../docs/data-layer/) — semantics and field dictionary.
