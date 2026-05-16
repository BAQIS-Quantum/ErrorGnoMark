-- Migration 0002: Observation / Inference / Forecast on observation_record (phase1_v1.1).

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'record_kind_enum') THEN
        CREATE TYPE record_kind_enum AS ENUM (
            'observation',
            'inference',
            'forecast'
        );
    END IF;
END $$;

ALTER TABLE observation_record
    ADD COLUMN IF NOT EXISTS record_kind record_kind_enum NOT NULL DEFAULT 'observation';

ALTER TABLE observation_record
    ADD COLUMN IF NOT EXISTS forecast_model_version TEXT,
    ADD COLUMN IF NOT EXISTS forecast_horizon_seconds INTEGER,
    ADD COLUMN IF NOT EXISTS forecast_metadata_json JSONB;

ALTER TABLE observation_record DROP CONSTRAINT IF EXISTS ck_observation_forecast_metadata;

ALTER TABLE observation_record
    ADD CONSTRAINT ck_observation_forecast_metadata
    CHECK (
        record_kind <> 'forecast'::record_kind_enum
        OR (
            forecast_model_version IS NOT NULL
            AND btrim(forecast_model_version) <> ''
        )
    );

CREATE INDEX IF NOT EXISTS idx_observation_record_kind_obstime
    ON observation_record (chip_id, record_kind, observation_time DESC);

INSERT INTO egm_schema_migration (version, description)
VALUES (
    '0002',
    'record_kind_enum + forecast metadata columns on observation_record'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
