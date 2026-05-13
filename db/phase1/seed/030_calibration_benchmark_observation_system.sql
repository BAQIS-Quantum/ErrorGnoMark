-- Phase 1 seed slice S1+S3: calibration_run/artifact, benchmark_run, observation_record,
-- calibration_snapshot, system_state (chip-alpha story).
-- Aligns with p1-step2 API-07..13 (Q8–Q18), API-10 Q12 (two benchmark_run rows for paging),
-- and API-11 Q13–Q14 (two observation rows for paging).
-- UUIDs must match src/egm/datastore/phase1_pg_constants.py
BEGIN;

-- Two calibration runs (newer first in ORDER BY start_time DESC)
INSERT INTO calibration_run (
    calibration_run_id,
    chip_id,
    run_type,
    target_scope_id,
    status,
    start_time,
    end_time,
    published_at,
    ingested_at,
    source_id,
    payload_json
) VALUES (
    'c1000001-0000-4000-8000-000000010001',
    'a0000001-0000-4000-8000-000000000001',
    'readout_cal',
    'f0000001-0000-4000-8000-000000010002',
    'succeeded',
    '2026-05-02T10:00:00Z',
    '2026-05-02T11:00:00Z',
    '2026-05-02T11:00:00Z',
    '2026-05-02T11:30:00Z',
    'b0000001-0000-4000-8000-000000000001',
    '{"seed":true}'::jsonb
),
(
    'c1000001-0000-4000-8000-000000010002',
    'a0000001-0000-4000-8000-000000000001',
    'gate_cal',
    NULL,
    'succeeded',
    '2026-05-08T14:00:00Z',
    '2026-05-08T15:30:00Z',
    '2026-05-08T15:30:00Z',
    '2026-05-08T16:00:00Z',
    'b0000001-0000-4000-8000-000000000001',
    '{"seed":true}'::jsonb
);

INSERT INTO calibration_artifact (
    calibration_artifact_id,
    calibration_run_id,
    chip_id,
    artifact_type,
    artifact_schema_name,
    target_scope_id,
    produced_at,
    published_at,
    ingested_at,
    effective_from,
    effective_to,
    payload_json,
    source_id
) VALUES (
    'c2000001-0000-4000-8000-000000010001',
    'c1000001-0000-4000-8000-000000010001',
    'a0000001-0000-4000-8000-000000000001',
    'readout_model',
    'readout.v1',
    'f0000001-0000-4000-8000-000000010002',
    '2026-05-02T11:00:00Z',
    '2026-05-02T11:00:00Z',
    '2026-05-02T11:30:00Z',
    NULL,
    NULL,
    '{"fidelity":0.99}'::jsonb,
    'b0000001-0000-4000-8000-000000000001'
),
(
    'c2000001-0000-4000-8000-000000010002',
    'c1000001-0000-4000-8000-000000010002',
    'a0000001-0000-4000-8000-000000000001',
    'gate_parameter',
    'gates.v1',
    NULL,
    '2026-05-08T15:30:00Z',
    '2026-05-08T15:30:00Z',
    '2026-05-08T16:00:00Z',
    NULL,
    NULL,
    '{"phase_error_rad":0.02}'::jsonb,
    'b0000001-0000-4000-8000-000000000001'
);

-- Two seeded benchmark runs (older + newer start_time; workflow may add more; verify uses >= 2)
INSERT INTO benchmark_run (
    benchmark_run_id,
    benchmark_name,
    benchmark_version_id,
    chip_id,
    target_scope_id,
    input_config_json,
    result_ref,
    status,
    start_time,
    end_time,
    ingested_at,
    source_id,
    payload_json
) VALUES (
    'b1000001-0000-4000-8000-000000010001',
    'xeb-demo-seed',
    NULL,
    'a0000001-0000-4000-8000-000000000001',
    NULL,
    '{"depth":3}'::jsonb,
    NULL,
    'succeeded',
    '2026-05-03T08:00:00Z',
    '2026-05-03T09:00:00Z',
    '2026-05-03T09:00:00Z',
    'b0000001-0000-4000-8000-000000000001',
    '{}'::jsonb
),
(
    'b1000001-0000-4000-8000-000000010002',
    'rb-demo-seed',
    NULL,
    'a0000001-0000-4000-8000-000000000001',
    NULL,
    '{"shots":1024}'::jsonb,
    NULL,
    'succeeded',
    '2026-05-10T08:00:00Z',
    '2026-05-10T09:00:00Z',
    '2026-05-10T09:00:00Z',
    'b0000001-0000-4000-8000-000000000001',
    '{}'::jsonb
);

-- Two observations on alpha q0, same metric, for API-11 window query
INSERT INTO observation_record (
    observation_record_id,
    chip_id,
    subject_type,
    subject_id,
    scope_id,
    metric_definition_id,
    producer_type,
    producer_id,
    value_numeric,
    unit,
    quality_flag,
    observation_time,
    published_at,
    ingested_at,
    source_id
) VALUES (
    '0b000002-0000-4000-8000-000000010001',
    'a0000001-0000-4000-8000-000000000001',
    'qubit',
    'd0000001-0000-4000-8000-000000010001',
    NULL,
    'c0000001-0000-4000-8000-000000000001',
    'benchmark_run',
    'b1000001-0000-4000-8000-000000010001',
    0.91,
    'dimensionless',
    'raw',
    '2026-05-02T12:00:00Z',
    NULL,
    '2026-05-02T13:00:00Z',
    'b0000001-0000-4000-8000-000000000001'
),
(
    '0b000002-0000-4000-8000-000000010002',
    'a0000001-0000-4000-8000-000000000001',
    'qubit',
    'd0000001-0000-4000-8000-000000010001',
    NULL,
    'c0000001-0000-4000-8000-000000000001',
    'benchmark_run',
    'b1000001-0000-4000-8000-000000010001',
    0.95,
    'dimensionless',
    'validated',
    '2026-05-03T10:00:00Z',
    NULL,
    '2026-05-03T11:00:00Z',
    'b0000001-0000-4000-8000-000000000001'
);

-- Calibration snapshots: superseded + current (scope_id NULL for simple latest query)
INSERT INTO calibration_snapshot (
    calibration_snapshot_id,
    chip_id,
    scope_id,
    snapshot_name,
    parameter_bundle_json,
    effective_from,
    effective_to,
    computed_at,
    ingested_at,
    source_id
) VALUES (
    'ca000002-0000-4000-8000-000000010001',
    'a0000001-0000-4000-8000-000000000001',
    NULL,
    'cal-seed-v0',
    '{"readout":{"amp":0.5}}'::jsonb,
    '2026-04-20T00:00:00Z',
    '2026-05-09T23:59:59Z',
    '2026-04-20T01:00:00Z',
    '2026-04-20T01:00:00Z',
    'b0000001-0000-4000-8000-000000000001'
),
(
    'ca000002-0000-4000-8000-000000010002',
    'a0000001-0000-4000-8000-000000000001',
    NULL,
    'cal-seed-v1',
    '{"readout":{"amp":0.52}}'::jsonb,
    '2026-05-10T00:00:00Z',
    NULL,
    '2026-05-10T01:00:00Z',
    '2026-05-10T01:00:00Z',
    'b0000001-0000-4000-8000-000000000001'
);

-- System states: closed row + current (FK to structure + calibration snapshots from seed 020/above)
INSERT INTO system_state (
    system_state_id,
    chip_id,
    time_anchor,
    effective_from,
    effective_to,
    structure_snapshot_id,
    calibration_snapshot_id,
    performance_summary_json,
    capacity_summary_json,
    state_summary_json,
    confidence,
    computed_at,
    ingested_at
) VALUES (
    'de000002-0000-4000-8000-000000010001',
    'a0000001-0000-4000-8000-000000000001',
    '2026-05-05T12:00:00Z',
    '2026-05-01T00:00:00Z',
    '2026-05-10T00:00:00Z',
    'f0000002-0000-4000-8000-000000010001',
    'ca000002-0000-4000-8000-000000010001',
    '{"t1":42}'::jsonb,
    '{}'::jsonb,
    '{"label":"seed-old"}'::jsonb,
    0.9000,
    '2026-05-05T12:00:00Z',
    '2026-05-05T12:00:00Z'
),
(
    'de000002-0000-4000-8000-000000010002',
    'a0000001-0000-4000-8000-000000000001',
    '2026-05-12T08:00:00Z',
    '2026-05-11T00:00:00Z',
    NULL,
    'f0000002-0000-4000-8000-000000010002',
    'ca000002-0000-4000-8000-000000010002',
    '{"t1":43}'::jsonb,
    '{}'::jsonb,
    '{"label":"seed-current"}'::jsonb,
    0.9500,
    '2026-05-12T08:00:00Z',
    '2026-05-12T08:00:00Z'
);

COMMIT;
