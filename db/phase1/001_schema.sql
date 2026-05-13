-- 《EGM Phase 1 最小表集 PostgreSQL DDL 草案 v1》
-- 目标：
-- 1) 将 EGM Phase 1 的最小表集转化为可执行 PostgreSQL DDL
-- 2) 优先支撑静态查询、时间语义和基础 lineage
-- 3) 以 PostgreSQL 14+ 为假定目标
--
-- 说明：
-- - 本草案优先强调“可落地、可查询、可演进”，不是最终极致范式化版本
-- - 大 payload 优先通过 payload_ref / raw_payload_ref 引用外部对象存储
-- - JSONB 用于承载暂不结构化或半结构化信息
-- - 时间字段统一使用 timestamptz
-- - 本草案包含：
--   * extension
--   * enum
--   * table
--   * constraint
--   * index
-- - 不包含：
--   * trigger
--   * 分区策略
--   * RLS
--   * 复杂物化视图
--
-- 建议执行顺序：
-- 1. extension
-- 2. enum
-- 3. base tables
-- 4. foreign key dependent tables
-- 5. indexes

BEGIN;

-- =========================================================
-- 0. Extensions
-- =========================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================================================
-- 1. Enums
-- =========================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'scope_type_enum') THEN
        CREATE TYPE scope_type_enum AS ENUM (
            'qubit',
            'coupler',
            'qubit_set',
            'subgraph',
            'chip',
            'mixed'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'source_type_enum') THEN
        CREATE TYPE source_type_enum AS ENUM (
            'vendor',
            'internal_pipeline',
            'manual_upload',
            'benchmark_system',
            'external_feed',
            'simulation',
            'other'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'version_change_type_enum') THEN
        CREATE TYPE version_change_type_enum AS ENUM (
            'create',
            'patch',
            'minor',
            'major',
            'deprecate',
            'retire',
            'backfill',
            'other'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'structure_event_type_enum') THEN
        CREATE TYPE structure_event_type_enum AS ENUM (
            'component_added',
            'component_removed',
            'component_updated',
            'edge_added',
            'edge_removed',
            'topology_changed',
            'scope_changed',
            'other'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'run_status_enum') THEN
        CREATE TYPE run_status_enum AS ENUM (
            'pending',
            'running',
            'succeeded',
            'failed',
            'cancelled',
            'partial'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'artifact_type_enum') THEN
        CREATE TYPE artifact_type_enum AS ENUM (
            'calibration_parameter',
            'readout_model',
            'gate_parameter',
            'noise_model',
            'fit_result',
            'report',
            'other'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'producer_type_enum') THEN
        CREATE TYPE producer_type_enum AS ENUM (
            'calibration_artifact',
            'benchmark_run',
            'external_feed',
            'manual'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subject_type_enum') THEN
        CREATE TYPE subject_type_enum AS ENUM (
            'chip',
            'qubit',
            'coupler',
            'scope'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'quality_flag_enum') THEN
        CREATE TYPE quality_flag_enum AS ENUM (
            'raw',
            'validated',
            'estimated',
            'derived',
            'suspect',
            'rejected'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lineage_transformation_type_enum') THEN
        CREATE TYPE lineage_transformation_type_enum AS ENUM (
            'event_to_snapshot',
            'artifact_to_snapshot',
            'observation_to_state',
            'snapshot_merge',
            'manual_curation',
            'backfill',
            'other'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lineage_object_type_enum') THEN
        CREATE TYPE lineage_object_type_enum AS ENUM (
            'structure_event',
            'calibration_run',
            'calibration_artifact',
            'benchmark_run',
            'observation_record',
            'structure_snapshot',
            'calibration_snapshot',
            'system_state'
        );
    END IF;
END
$$;

-- =========================================================
-- 2. Core entity tables
-- =========================================================

CREATE TABLE IF NOT EXISTS chip (
    chip_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chip_name                TEXT NOT NULL,
    generation_name          TEXT,
    serial_number            TEXT,
    vendor                   TEXT,
    status                   TEXT NOT NULL DEFAULT 'active',
    fabrication_info_json    JSONB NOT NULL DEFAULT '{}'::jsonb,
    commission_time          TIMESTAMPTZ,
    retire_time              TIMESTAMPTZ,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_chip_name UNIQUE (chip_name),
    CONSTRAINT uq_chip_serial_number UNIQUE (serial_number),
    CONSTRAINT ck_chip_commission_retire
        CHECK (retire_time IS NULL OR commission_time IS NULL OR retire_time >= commission_time)
);

CREATE TABLE IF NOT EXISTS qubit (
    qubit_id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chip_id                  UUID NOT NULL REFERENCES chip(chip_id) ON DELETE CASCADE,
    qubit_index              INTEGER NOT NULL,
    qubit_label              TEXT,
    role_tags_json           JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_qubit_chip_index UNIQUE (chip_id, qubit_index)
);

CREATE TABLE IF NOT EXISTS coupler (
    coupler_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chip_id                  UUID NOT NULL REFERENCES chip(chip_id) ON DELETE CASCADE,
    coupler_name             TEXT,
    coupler_type             TEXT,
    metadata_json            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS coupler_endpoint (
    coupler_endpoint_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coupler_id               UUID NOT NULL REFERENCES coupler(coupler_id) ON DELETE CASCADE,
    qubit_id                 UUID NOT NULL REFERENCES qubit(qubit_id) ON DELETE CASCADE,
    endpoint_order           SMALLINT NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_coupler_qubit UNIQUE (coupler_id, qubit_id),
    CONSTRAINT uq_coupler_endpoint_order UNIQUE (coupler_id, endpoint_order),
    CONSTRAINT ck_endpoint_order_nonnegative CHECK (endpoint_order >= 0)
);

CREATE TABLE IF NOT EXISTS scope (
    scope_id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chip_id                  UUID REFERENCES chip(chip_id) ON DELETE CASCADE,
    scope_type               scope_type_enum NOT NULL,
    scope_name               TEXT NOT NULL,
    description              TEXT,
    scope_payload_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_scope_name_per_chip UNIQUE (chip_id, scope_name)
);

-- 可选：为对象到 scope 的静态归属提供显式映射
CREATE TABLE IF NOT EXISTS scope_member (
    scope_member_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_id                 UUID NOT NULL REFERENCES scope(scope_id) ON DELETE CASCADE,
    member_type              subject_type_enum NOT NULL,
    member_id                UUID NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_scope_member UNIQUE (scope_id, member_type, member_id)
);

-- =========================================================
-- 3. Governance / definition tables
-- =========================================================

CREATE TABLE IF NOT EXISTS source (
    source_id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name              TEXT NOT NULL,
    source_type              source_type_enum NOT NULL,
    owner_name               TEXT,
    trust_level              INTEGER,
    source_config_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_source_name UNIQUE (source_name),
    CONSTRAINT ck_source_trust_level CHECK (trust_level IS NULL OR (trust_level >= 0 AND trust_level <= 100))
);

CREATE TABLE IF NOT EXISTS version (
    version_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_family            TEXT NOT NULL,
    object_name              TEXT NOT NULL,
    semantic_version         TEXT NOT NULL,
    parent_version_id        UUID REFERENCES version(version_id) ON DELETE SET NULL,
    change_type              version_change_type_enum NOT NULL DEFAULT 'create',
    change_summary           TEXT,
    version_created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    version_released_at      TIMESTAMPTZ,
    version_effective_from   TIMESTAMPTZ,
    version_effective_to     TIMESTAMPTZ,
    is_current               BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT uq_version_object_semver UNIQUE (object_family, object_name, semantic_version),
    CONSTRAINT ck_version_effective_range
        CHECK (version_effective_to IS NULL OR version_effective_from IS NULL OR version_effective_to > version_effective_from)
);

CREATE TABLE IF NOT EXISTS metric_definition (
    metric_definition_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name              TEXT NOT NULL,
    metric_family            TEXT,
    value_type               TEXT NOT NULL, -- e.g. numeric/text/json
    unit                     TEXT,
    description              TEXT,
    target_scope_type        scope_type_enum,
    version_id               UUID REFERENCES version(version_id) ON DELETE SET NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_metric_name UNIQUE (metric_name)
);

-- =========================================================
-- 4. Fact tables
-- =========================================================

CREATE TABLE IF NOT EXISTS structure_event (
    structure_event_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chip_id                  UUID NOT NULL REFERENCES chip(chip_id) ON DELETE CASCADE,
    event_type               structure_event_type_enum NOT NULL,
    change_summary           TEXT,
    changed_scope_id         UUID REFERENCES scope(scope_id) ON DELETE SET NULL,
    event_time               TIMESTAMPTZ NOT NULL,
    effective_time           TIMESTAMPTZ,
    published_at             TIMESTAMPTZ,
    ingested_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_id                UUID NOT NULL REFERENCES source(source_id) ON DELETE RESTRICT,
    raw_payload_ref          TEXT,
    payload_json             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_structure_event_times
        CHECK (published_at IS NULL OR published_at <= ingested_at)
);

CREATE TABLE IF NOT EXISTS calibration_run (
    calibration_run_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chip_id                  UUID NOT NULL REFERENCES chip(chip_id) ON DELETE CASCADE,
    run_type                 TEXT NOT NULL,
    target_scope_id          UUID REFERENCES scope(scope_id) ON DELETE SET NULL,
    status                   run_status_enum NOT NULL DEFAULT 'pending',
    start_time               TIMESTAMPTZ NOT NULL,
    end_time                 TIMESTAMPTZ,
    published_at             TIMESTAMPTZ,
    ingested_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_id                UUID NOT NULL REFERENCES source(source_id) ON DELETE RESTRICT,
    raw_payload_ref          TEXT,
    payload_json             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_calibration_run_time CHECK (end_time IS NULL OR end_time >= start_time),
    CONSTRAINT ck_calibration_run_publish_ingest CHECK (published_at IS NULL OR published_at <= ingested_at)
);

CREATE TABLE IF NOT EXISTS calibration_artifact (
    calibration_artifact_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calibration_run_id       UUID NOT NULL REFERENCES calibration_run(calibration_run_id) ON DELETE CASCADE,
    chip_id                  UUID NOT NULL REFERENCES chip(chip_id) ON DELETE CASCADE,
    artifact_type            artifact_type_enum NOT NULL,
    artifact_schema_name     TEXT,
    target_scope_id          UUID REFERENCES scope(scope_id) ON DELETE SET NULL,
    produced_at              TIMESTAMPTZ NOT NULL,
    published_at             TIMESTAMPTZ,
    ingested_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_from           TIMESTAMPTZ,
    effective_to             TIMESTAMPTZ,
    payload_json             JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_ref              TEXT,
    source_id                UUID NOT NULL REFERENCES source(source_id) ON DELETE RESTRICT,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_calibration_artifact_effective_range
        CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from),
    CONSTRAINT ck_calibration_artifact_publish_ingest
        CHECK (published_at IS NULL OR published_at <= ingested_at)
);

CREATE TABLE IF NOT EXISTS benchmark_run (
    benchmark_run_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    benchmark_name           TEXT NOT NULL,
    benchmark_version_id     UUID REFERENCES version(version_id) ON DELETE SET NULL,
    chip_id                  UUID NOT NULL REFERENCES chip(chip_id) ON DELETE CASCADE,
    target_scope_id          UUID REFERENCES scope(scope_id) ON DELETE SET NULL,
    input_config_json        JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_ref               TEXT,
    status                   run_status_enum NOT NULL DEFAULT 'pending',
    start_time               TIMESTAMPTZ NOT NULL,
    end_time                 TIMESTAMPTZ,
    ingested_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_id                UUID NOT NULL REFERENCES source(source_id) ON DELETE RESTRICT,
    payload_json             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_benchmark_run_time CHECK (end_time IS NULL OR end_time >= start_time)
);

CREATE TABLE IF NOT EXISTS observation_record (
    observation_record_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chip_id                  UUID NOT NULL REFERENCES chip(chip_id) ON DELETE CASCADE,
    subject_type             subject_type_enum NOT NULL,
    subject_id               UUID NOT NULL,
    scope_id                 UUID REFERENCES scope(scope_id) ON DELETE SET NULL,
    metric_definition_id     UUID NOT NULL REFERENCES metric_definition(metric_definition_id) ON DELETE RESTRICT,
    producer_type            producer_type_enum NOT NULL,
    producer_id              UUID NOT NULL,
    value_numeric            DOUBLE PRECISION,
    value_text               TEXT,
    value_json               JSONB,
    unit                     TEXT,
    quality_flag             quality_flag_enum NOT NULL DEFAULT 'raw',
    observation_time         TIMESTAMPTZ NOT NULL,
    effective_from           TIMESTAMPTZ,
    effective_to             TIMESTAMPTZ,
    published_at             TIMESTAMPTZ,
    ingested_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_id                UUID NOT NULL REFERENCES source(source_id) ON DELETE RESTRICT,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_observation_effective_range
        CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from),
    CONSTRAINT ck_observation_value_presence
        CHECK (
            value_numeric IS NOT NULL
            OR value_text IS NOT NULL
            OR value_json IS NOT NULL
        ),
    CONSTRAINT ck_observation_publish_ingest
        CHECK (published_at IS NULL OR published_at <= ingested_at)
);

-- =========================================================
-- 5. Snapshot / state tables
-- =========================================================

CREATE TABLE IF NOT EXISTS structure_snapshot (
    structure_snapshot_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chip_id                  UUID NOT NULL REFERENCES chip(chip_id) ON DELETE CASCADE,
    scope_id                 UUID REFERENCES scope(scope_id) ON DELETE SET NULL,
    component_manifest_json  JSONB NOT NULL DEFAULT '{}'::jsonb,
    edge_manifest_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
    effective_from           TIMESTAMPTZ NOT NULL,
    effective_to             TIMESTAMPTZ,
    computed_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    ingested_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_id                UUID REFERENCES source(source_id) ON DELETE SET NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_structure_snapshot_effective_range
        CHECK (effective_to IS NULL OR effective_to > effective_from)
);

CREATE TABLE IF NOT EXISTS calibration_snapshot (
    calibration_snapshot_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chip_id                  UUID NOT NULL REFERENCES chip(chip_id) ON DELETE CASCADE,
    scope_id                 UUID REFERENCES scope(scope_id) ON DELETE SET NULL,
    snapshot_name            TEXT,
    parameter_bundle_json    JSONB NOT NULL DEFAULT '{}'::jsonb,
    effective_from           TIMESTAMPTZ NOT NULL,
    effective_to             TIMESTAMPTZ,
    computed_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    ingested_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_id                UUID REFERENCES source(source_id) ON DELETE SET NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_calibration_snapshot_effective_range
        CHECK (effective_to IS NULL OR effective_to > effective_from)
);

CREATE TABLE IF NOT EXISTS system_state (
    system_state_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chip_id                  UUID NOT NULL REFERENCES chip(chip_id) ON DELETE CASCADE,
    time_anchor              TIMESTAMPTZ NOT NULL,
    effective_from           TIMESTAMPTZ NOT NULL,
    effective_to             TIMESTAMPTZ,
    structure_snapshot_id    UUID REFERENCES structure_snapshot(structure_snapshot_id) ON DELETE SET NULL,
    calibration_snapshot_id  UUID REFERENCES calibration_snapshot(calibration_snapshot_id) ON DELETE SET NULL,
    performance_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    capacity_summary_json    JSONB NOT NULL DEFAULT '{}'::jsonb,
    state_summary_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence               NUMERIC(5,4),
    computed_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    ingested_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_system_state_effective_range
        CHECK (effective_to IS NULL OR effective_to > effective_from),
    CONSTRAINT ck_system_state_confidence
        CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

-- =========================================================
-- 6. Lineage tables
-- =========================================================

CREATE TABLE IF NOT EXISTS lineage (
    lineage_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    downstream_object_type   lineage_object_type_enum NOT NULL,
    downstream_object_id     UUID NOT NULL,
    transformation_type      lineage_transformation_type_enum NOT NULL,
    method_version_id        UUID REFERENCES version(version_id) ON DELETE SET NULL,
    computed_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_lineage_downstream UNIQUE (downstream_object_type, downstream_object_id)
);

CREATE TABLE IF NOT EXISTS lineage_edge (
    lineage_edge_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lineage_id               UUID NOT NULL REFERENCES lineage(lineage_id) ON DELETE CASCADE,
    upstream_object_type     lineage_object_type_enum NOT NULL,
    upstream_object_id       UUID NOT NULL,
    edge_role                TEXT,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_lineage_edge UNIQUE (lineage_id, upstream_object_type, upstream_object_id, edge_role)
);

-- =========================================================
-- 7. Helpful indexes
-- =========================================================

-- chip / qubit / coupler
CREATE INDEX IF NOT EXISTS idx_qubit_chip_id
    ON qubit (chip_id);

CREATE INDEX IF NOT EXISTS idx_coupler_chip_id
    ON coupler (chip_id);

CREATE INDEX IF NOT EXISTS idx_coupler_endpoint_coupler_id
    ON coupler_endpoint (coupler_id);

CREATE INDEX IF NOT EXISTS idx_coupler_endpoint_qubit_id
    ON coupler_endpoint (qubit_id);

CREATE INDEX IF NOT EXISTS idx_scope_chip_id
    ON scope (chip_id);

CREATE INDEX IF NOT EXISTS idx_scope_member_member
    ON scope_member (member_type, member_id);

-- version / metric
CREATE INDEX IF NOT EXISTS idx_version_object_current
    ON version (object_family, object_name, is_current);

CREATE INDEX IF NOT EXISTS idx_version_effective_range
    ON version (version_effective_from, version_effective_to);

CREATE INDEX IF NOT EXISTS idx_metric_definition_family
    ON metric_definition (metric_family);

-- structure_event
CREATE INDEX IF NOT EXISTS idx_structure_event_chip_event_time
    ON structure_event (chip_id, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_structure_event_chip_effective_time
    ON structure_event (chip_id, effective_time DESC);

CREATE INDEX IF NOT EXISTS idx_structure_event_ingested_at
    ON structure_event (ingested_at DESC);

-- calibration_run
CREATE INDEX IF NOT EXISTS idx_calibration_run_chip_start_time
    ON calibration_run (chip_id, start_time DESC);

CREATE INDEX IF NOT EXISTS idx_calibration_run_target_scope
    ON calibration_run (target_scope_id);

CREATE INDEX IF NOT EXISTS idx_calibration_run_ingested_at
    ON calibration_run (ingested_at DESC);

-- calibration_artifact
CREATE INDEX IF NOT EXISTS idx_calibration_artifact_run_id
    ON calibration_artifact (calibration_run_id);

CREATE INDEX IF NOT EXISTS idx_calibration_artifact_chip_effective
    ON calibration_artifact (chip_id, effective_from DESC, effective_to);

CREATE INDEX IF NOT EXISTS idx_calibration_artifact_target_scope
    ON calibration_artifact (target_scope_id);

CREATE INDEX IF NOT EXISTS idx_calibration_artifact_ingested_at
    ON calibration_artifact (ingested_at DESC);

-- benchmark_run
CREATE INDEX IF NOT EXISTS idx_benchmark_run_chip_start_time
    ON benchmark_run (chip_id, start_time DESC);

CREATE INDEX IF NOT EXISTS idx_benchmark_run_name_start_time
    ON benchmark_run (benchmark_name, start_time DESC);

CREATE INDEX IF NOT EXISTS idx_benchmark_run_target_scope
    ON benchmark_run (target_scope_id);

-- observation_record
CREATE INDEX IF NOT EXISTS idx_observation_chip_metric_obstime
    ON observation_record (chip_id, metric_definition_id, observation_time DESC);

CREATE INDEX IF NOT EXISTS idx_observation_subject_obstime
    ON observation_record (subject_type, subject_id, observation_time DESC);

CREATE INDEX IF NOT EXISTS idx_observation_scope_obstime
    ON observation_record (scope_id, observation_time DESC);

CREATE INDEX IF NOT EXISTS idx_observation_producer
    ON observation_record (producer_type, producer_id);

CREATE INDEX IF NOT EXISTS idx_observation_ingested_at
    ON observation_record (ingested_at DESC);

CREATE INDEX IF NOT EXISTS idx_observation_effective_range
    ON observation_record (effective_from, effective_to);

-- structure_snapshot
CREATE INDEX IF NOT EXISTS idx_structure_snapshot_chip_effective
    ON structure_snapshot (chip_id, effective_from DESC, effective_to);

CREATE INDEX IF NOT EXISTS idx_structure_snapshot_scope_effective
    ON structure_snapshot (scope_id, effective_from DESC, effective_to);

CREATE INDEX IF NOT EXISTS idx_structure_snapshot_ingested_at
    ON structure_snapshot (ingested_at DESC);

-- calibration_snapshot
CREATE INDEX IF NOT EXISTS idx_calibration_snapshot_chip_effective
    ON calibration_snapshot (chip_id, effective_from DESC, effective_to);

CREATE INDEX IF NOT EXISTS idx_calibration_snapshot_scope_effective
    ON calibration_snapshot (scope_id, effective_from DESC, effective_to);

CREATE INDEX IF NOT EXISTS idx_calibration_snapshot_ingested_at
    ON calibration_snapshot (ingested_at DESC);

-- system_state
CREATE INDEX IF NOT EXISTS idx_system_state_chip_effective
    ON system_state (chip_id, effective_from DESC, effective_to);

CREATE INDEX IF NOT EXISTS idx_system_state_chip_time_anchor
    ON system_state (chip_id, time_anchor DESC);

CREATE INDEX IF NOT EXISTS idx_system_state_ingested_at
    ON system_state (ingested_at DESC);

-- lineage
CREATE INDEX IF NOT EXISTS idx_lineage_downstream
    ON lineage (downstream_object_type, downstream_object_id);

CREATE INDEX IF NOT EXISTS idx_lineage_edge_lineage_id
    ON lineage_edge (lineage_id);

CREATE INDEX IF NOT EXISTS idx_lineage_edge_upstream
    ON lineage_edge (upstream_object_type, upstream_object_id);

-- =========================================================
-- 8. Optional helper views for current effective records
-- =========================================================

CREATE OR REPLACE VIEW v_current_structure_snapshot AS
SELECT ss.*
FROM structure_snapshot ss
WHERE ss.effective_to IS NULL;

CREATE OR REPLACE VIEW v_current_calibration_snapshot AS
SELECT cs.*
FROM calibration_snapshot cs
WHERE cs.effective_to IS NULL;

CREATE OR REPLACE VIEW v_current_system_state AS
SELECT st.*
FROM system_state st
WHERE st.effective_to IS NULL;

COMMIT;

