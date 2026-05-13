-- Phase 1 seed: lineage for current system_state (API-14 / Q19–Q21 slice).
-- UUIDs must match src/egm/datastore/phase1_pg_constants.py
BEGIN;

INSERT INTO lineage (
    lineage_id,
    downstream_object_type,
    downstream_object_id,
    transformation_type,
    method_version_id,
    computed_at
) VALUES (
    '1a000002-0000-4000-8000-000000010001',
    'system_state',
    'de000002-0000-4000-8000-000000010002',
    'snapshot_merge',
    NULL,
    '2026-05-12T09:00:00Z'
);

INSERT INTO lineage_edge (
    lineage_edge_id,
    lineage_id,
    upstream_object_type,
    upstream_object_id,
    edge_role
) VALUES (
    '1e000002-0000-4000-8000-000000010001',
    '1a000002-0000-4000-8000-000000010001',
    'structure_snapshot',
    'f0000002-0000-4000-8000-000000010002',
    'input_structure'
),
(
    '1e000002-0000-4000-8000-000000010002',
    '1a000002-0000-4000-8000-000000010001',
    'calibration_snapshot',
    'ca000002-0000-4000-8000-000000010002',
    'input_calibration'
);

COMMIT;
