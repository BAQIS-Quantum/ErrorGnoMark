-- Minimal Phase 1 demo rows (spine A+B+D and PG workflow smoke).
-- UUIDs must match src/egm/datastore/phase1_pg_constants.py
BEGIN;

INSERT INTO source (
    source_id, source_name, source_type, owner_name, trust_level, source_config_json
) VALUES (
    'b0000001-0000-4000-8000-000000000001',
    'egm-phase1-seed',
    'internal_pipeline',
    'egm',
    100,
    '{}'::jsonb
);

INSERT INTO metric_definition (
    metric_definition_id,
    metric_name,
    metric_family,
    value_type,
    unit,
    description,
    target_scope_type,
    version_id
) VALUES (
    'c0000001-0000-4000-8000-000000000001',
    'egm.workflow.task_observation.v1',
    'egm_workflow',
    'json',
    NULL,
    'Task-level observation payload (EGM workflow); value_json mirrors ObservationPersistenceDict.',
    'chip',
    NULL
);

INSERT INTO chip (
    chip_id, chip_name, generation_name, serial_number, vendor, status,
    fabrication_info_json, commission_time, retire_time
) VALUES
(
    'a0000001-0000-4000-8000-000000000001',
    'chip-alpha',
    'gen-demo',
    NULL,
    'demo',
    'active',
    '{}'::jsonb,
    '2026-04-01T00:00:00Z',
    NULL
),
(
    'a0000001-0000-4000-8000-000000000002',
    'chip-beta',
    'gen-demo',
    NULL,
    'demo',
    'active',
    '{}'::jsonb,
    '2026-04-01T00:00:00Z',
    NULL
);

-- alpha qubits 0..3
INSERT INTO qubit (qubit_id, chip_id, qubit_index, qubit_label, role_tags_json) VALUES
('d0000001-0000-4000-8000-000000010001', 'a0000001-0000-4000-8000-000000000001', 0, 'alpha-q0', '[]'::jsonb),
('d0000001-0000-4000-8000-000000010002', 'a0000001-0000-4000-8000-000000000001', 1, 'alpha-q1', '[]'::jsonb),
('d0000001-0000-4000-8000-000000010003', 'a0000001-0000-4000-8000-000000000001', 2, 'alpha-q2', '[]'::jsonb),
('d0000001-0000-4000-8000-000000010004', 'a0000001-0000-4000-8000-000000000001', 3, 'alpha-q3', '[]'::jsonb);

-- beta qubits 0..3
INSERT INTO qubit (qubit_id, chip_id, qubit_index, qubit_label, role_tags_json) VALUES
('d0000001-0000-4000-8000-000000020001', 'a0000001-0000-4000-8000-000000000002', 0, 'beta-q0', '[]'::jsonb),
('d0000001-0000-4000-8000-000000020002', 'a0000001-0000-4000-8000-000000000002', 1, 'beta-q1', '[]'::jsonb),
('d0000001-0000-4000-8000-000000020003', 'a0000001-0000-4000-8000-000000000002', 2, 'beta-q2', '[]'::jsonb),
('d0000001-0000-4000-8000-000000020004', 'a0000001-0000-4000-8000-000000000002', 3, 'beta-q3', '[]'::jsonb);

-- alpha couplers + endpoints (linear 0-1-2-3)
INSERT INTO coupler (coupler_id, chip_id, coupler_name, coupler_type, metadata_json) VALUES
('e0000001-0000-4000-8000-000000010001', 'a0000001-0000-4000-8000-000000000001', 'alpha-c01', 'bus', '{}'::jsonb),
('e0000001-0000-4000-8000-000000010002', 'a0000001-0000-4000-8000-000000000001', 'alpha-c12', 'bus', '{}'::jsonb),
('e0000001-0000-4000-8000-000000010003', 'a0000001-0000-4000-8000-000000000001', 'alpha-c23', 'bus', '{}'::jsonb);

INSERT INTO coupler_endpoint (coupler_endpoint_id, coupler_id, qubit_id, endpoint_order) VALUES
('ee000001-0000-4000-8000-000000010001', 'e0000001-0000-4000-8000-000000010001', 'd0000001-0000-4000-8000-000000010001', 0),
('ee000001-0000-4000-8000-000000010002', 'e0000001-0000-4000-8000-000000010001', 'd0000001-0000-4000-8000-000000010002', 1),
('ee000001-0000-4000-8000-000000010003', 'e0000001-0000-4000-8000-000000010002', 'd0000001-0000-4000-8000-000000010002', 0),
('ee000001-0000-4000-8000-000000010004', 'e0000001-0000-4000-8000-000000010002', 'd0000001-0000-4000-8000-000000010003', 1),
('ee000001-0000-4000-8000-000000010005', 'e0000001-0000-4000-8000-000000010003', 'd0000001-0000-4000-8000-000000010003', 0),
('ee000001-0000-4000-8000-000000010006', 'e0000001-0000-4000-8000-000000010003', 'd0000001-0000-4000-8000-000000010004', 1);

-- beta couplers + endpoints
INSERT INTO coupler (coupler_id, chip_id, coupler_name, coupler_type, metadata_json) VALUES
('e0000001-0000-4000-8000-000000020001', 'a0000001-0000-4000-8000-000000000002', 'beta-c01', 'bus', '{}'::jsonb),
('e0000001-0000-4000-8000-000000020002', 'a0000001-0000-4000-8000-000000000002', 'beta-c12', 'bus', '{}'::jsonb),
('e0000001-0000-4000-8000-000000020003', 'a0000001-0000-4000-8000-000000000002', 'beta-c23', 'bus', '{}'::jsonb);

INSERT INTO coupler_endpoint (coupler_endpoint_id, coupler_id, qubit_id, endpoint_order) VALUES
('ee000001-0000-4000-8000-000000020001', 'e0000001-0000-4000-8000-000000020001', 'd0000001-0000-4000-8000-000000020001', 0),
('ee000001-0000-4000-8000-000000020002', 'e0000001-0000-4000-8000-000000020001', 'd0000001-0000-4000-8000-000000020002', 1),
('ee000001-0000-4000-8000-000000020003', 'e0000001-0000-4000-8000-000000020002', 'd0000001-0000-4000-8000-000000020002', 0),
('ee000001-0000-4000-8000-000000020004', 'e0000001-0000-4000-8000-000000020002', 'd0000001-0000-4000-8000-000000020003', 1),
('ee000001-0000-4000-8000-000000020005', 'e0000001-0000-4000-8000-000000020003', 'd0000001-0000-4000-8000-000000020003', 0),
('ee000001-0000-4000-8000-000000020006', 'e0000001-0000-4000-8000-000000020003', 'd0000001-0000-4000-8000-000000020004', 1);

INSERT INTO scope (scope_id, chip_id, scope_type, scope_name, description, scope_payload_json) VALUES
('f0000001-0000-4000-8000-000000010001', 'a0000001-0000-4000-8000-000000000001', 'chip', 'alpha-chip-scope', NULL, '{}'::jsonb),
('f0000001-0000-4000-8000-000000010002', 'a0000001-0000-4000-8000-000000000001', 'qubit_set', 'alpha-left-pair', NULL, '{"qubits":[0,1]}'::jsonb),
('f0000001-0000-4000-8000-000000020001', 'a0000001-0000-4000-8000-000000000002', 'chip', 'beta-chip-scope', NULL, '{}'::jsonb),
('f0000001-0000-4000-8000-000000020002', 'a0000001-0000-4000-8000-000000000002', 'qubit_set', 'beta-left-pair', NULL, '{"qubits":[0,1]}'::jsonb);

COMMIT;
