# PostgreSQL schema migration policy (Phase 1)

## Versioning

- **Target version:** `db/schema_version.txt` (e.g. `0002` → `phase1_v1.1`).
- **Applied versions:** rows in `egm_schema_migration`.
- **Bootstrap:** `db/phase1/001_schema.sql` + `db/phase1/seed/*.sql` = logical `phase1_v1.0` base tables.

## Fresh database

```bash
export EGM_PG_DSN='postgresql://user:pass@localhost:5432/egm_phase1'
./scripts/postgres/apply_phase1.sh
```

This applies DDL, seed, then `apply_migrations.py` (0001 → target).

## Upgrade existing database

If you already applied Phase 1 before Horizon E:

```bash
export EGM_PG_DSN='...'
python scripts/postgres/apply_migrations.py
python -m egm.datastore.phase1_acceptance --strict
```

No seed re-run required. Existing `observation_record` rows receive `record_kind = observation` by default.

## Rollback

- Migrations are **forward-only** by default.
- Each file should document reversibility in a header comment.
- **Development:** drop and recreate the database, then `apply_phase1.sh`.
- **Production:** do not rely on `DROP DATABASE`; plan forward migrations with Athena review for breaking changes.

## Breaking change checklist

1. New file `db/migrations/NNNN_description.sql`.
2. Bump `db/schema_version.txt`.
3. Update `docs/data-layer/observation-schema.md` and [sql/queries/README.md](../sql/queries/README.md).
4. Run `phase1_acceptance --strict`.
5. CHANGELOG entry.

## Query compatibility

P0 templates under `sql/queries/p0/` are validated against the schema version in CI. New columns must not break existing queries (defaults / nullable).
