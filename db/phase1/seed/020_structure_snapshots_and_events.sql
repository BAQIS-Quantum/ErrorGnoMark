-- Phase 1 seed slice S1: structure_snapshot + structure_event for chip-alpha.
-- Supports p1-step2 API-05 (Q5/Q6), API-06 (Q7 + filtered Q7), and snapshot/event seed ids in phase1_pg_constants.
-- UUIDs must match src/egm/datastore/phase1_pg_constants.py
BEGIN;

-- Two structure_snapshot rows: superseded window + current open-ended (latest).
INSERT INTO structure_snapshot (
    structure_snapshot_id,
    chip_id,
    scope_id,
    component_manifest_json,
    edge_manifest_json,
    effective_from,
    effective_to,
    computed_at,
    ingested_at,
    source_id
) VALUES (
    'f0000002-0000-4000-8000-000000010001',
    'a0000001-0000-4000-8000-000000000001',
    NULL,
    '{"version":"v0-demo","qubits":4}'::jsonb,
    '{}'::jsonb,
    '2026-04-01T00:00:00Z',
    '2026-04-15T23:59:59Z',
    '2026-04-01T01:00:00Z',
    '2026-04-01T01:00:00Z',
    'b0000001-0000-4000-8000-000000000001'
),
(
    'f0000002-0000-4000-8000-000000010002',
    'a0000001-0000-4000-8000-000000000001',
    NULL,
    '{"version":"v1-demo","qubits":4}'::jsonb,
    '{}'::jsonb,
    '2026-04-16T00:00:00Z',
    NULL,
    '2026-04-16T01:00:00Z',
    '2026-04-16T01:00:00Z',
    'b0000001-0000-4000-8000-000000000001'
);

INSERT INTO structure_event (
    structure_event_id,
    chip_id,
    event_type,
    change_summary,
    changed_scope_id,
    event_time,
    effective_time,
    published_at,
    ingested_at,
    source_id,
    payload_json
) VALUES (
    'e0000002-0000-4000-8000-000000010001',
    'a0000001-0000-4000-8000-000000000001',
    'topology_changed',
    'seed: initial topology story',
    NULL,
    '2026-04-02T12:00:00Z',
    NULL,
    '2026-04-02T12:00:00Z',
    '2026-04-02T13:00:00Z',
    'b0000001-0000-4000-8000-000000000001',
    '{}'::jsonb
),
(
    'e0000002-0000-4000-8000-000000010002',
    'a0000001-0000-4000-8000-000000000001',
    'component_added',
    'seed: post-snapshot wiring',
    NULL,
    '2026-04-18T09:00:00Z',
    NULL,
    '2026-04-18T09:00:00Z',
    '2026-04-18T10:00:00Z',
    'b0000001-0000-4000-8000-000000000001',
    '{}'::jsonb
);

COMMIT;
