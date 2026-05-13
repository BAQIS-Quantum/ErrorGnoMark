-- Quafu Baihua chip bootstrap: chip + source + metric_definition × 5.
-- UUIDs must match src/egm/datastore/phase1_pg_constants.py
-- Qubit / coupler rows are created by the ingest script (156+182 too many to hardcode).
BEGIN;

-- ── Source: Quafu official calibration feed ──────────────────────────────────
INSERT INTO source (
    source_id, source_name, source_type, owner_name, trust_level, source_config_json
) VALUES (
    'b0000001-0000-4000-8000-000000000002',
    'quafu_baihua_calibration',
    'external_feed',
    'BAQIS / Quafu',
    80,
    '{"url": "https://quafu-sqc.baqis.ac.cn/chipDetails?chip=Baihua"}'::jsonb
)
ON CONFLICT (source_name) DO NOTHING;

-- ── Chip: Baihua ─────────────────────────────────────────────────────────────
INSERT INTO chip (
    chip_id, chip_name, generation_name, serial_number, vendor, status,
    fabrication_info_json, commission_time, retire_time
) VALUES (
    'a0000001-0000-4000-8000-000000000003',
    'Baihua',
    'quafu-156q',
    NULL,
    'BAQIS',
    'active',
    '{
        "available_qubits": 156,
        "couplers": 182,
        "basis_gates": ["h","rx","ry","rz","cz"],
        "platform": "Quafu Superconducting Quantum Computing"
    }'::jsonb,
    NULL,
    NULL
)
ON CONFLICT (chip_name) DO NOTHING;

-- ── Scope: whole-chip scope for Baihua ───────────────────────────────────────
INSERT INTO scope (
    scope_id, chip_id, scope_type, scope_name, description, scope_payload_json
) VALUES (
    'f0000001-0000-4000-8000-000000030001',
    'a0000001-0000-4000-8000-000000000003',
    'chip',
    'baihua-chip-scope',
    'Whole-chip scope for Baihua (156 qubits)',
    '{}'::jsonb
)
ON CONFLICT (chip_id, scope_name) DO NOTHING;

-- ── Metric definitions: 5 Quafu calibration metrics ─────────────────────────
INSERT INTO metric_definition (
    metric_definition_id, metric_name, metric_family,
    value_type, unit, description, target_scope_type, version_id
) VALUES
(
    'c0000001-0000-4000-8000-000000000002',
    'quafu_t1',
    'quafu_calibration',
    'numeric',
    'us',
    'T1 relaxation time from Quafu official calibration',
    'qubit',
    NULL
),
(
    'c0000001-0000-4000-8000-000000000003',
    'quafu_t2',
    'quafu_calibration',
    'numeric',
    'us',
    'T2 dephasing time from Quafu official calibration',
    'qubit',
    NULL
),
(
    'c0000001-0000-4000-8000-000000000004',
    'quafu_frequency',
    'quafu_calibration',
    'numeric',
    'GHz',
    'Qubit operating frequency from Quafu official calibration',
    'qubit',
    NULL
),
(
    'c0000001-0000-4000-8000-000000000005',
    'quafu_single_qubit_fidelity',
    'quafu_calibration',
    'numeric',
    'dimensionless',
    'Single-qubit gate fidelity from Quafu official calibration',
    'qubit',
    NULL
),
(
    'c0000001-0000-4000-8000-000000000006',
    'quafu_cz_fidelity',
    'quafu_calibration',
    'numeric',
    'dimensionless',
    'CZ gate fidelity per coupler from Quafu official calibration',
    'coupler',
    NULL
)
ON CONFLICT (metric_name) DO NOTHING;

COMMIT;
