-- p1-step2 API-08 / Q9: artifacts for a calibration run
-- Params: calibration_run_id (uuid)
SELECT
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
    payload_ref,
    source_id,
    created_at
FROM calibration_artifact
WHERE calibration_run_id = %(calibration_run_id)s::uuid
ORDER BY produced_at DESC, calibration_artifact_id;
