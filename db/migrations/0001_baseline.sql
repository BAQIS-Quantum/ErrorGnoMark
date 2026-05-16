-- Migration 0001: schema version registry (Phase 1 bootstrap marker).
-- Apply after db/phase1/001_schema.sql + seed via apply_phase1.sh.

BEGIN;

CREATE TABLE IF NOT EXISTS egm_schema_migration (
    version     TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    description TEXT NOT NULL
);

INSERT INTO egm_schema_migration (version, description)
VALUES (
    '0001',
    'Phase 1 bootstrap (001_schema.sql + seed via apply_phase1.sh)'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
