-- p1-step2 API-09 / Q10: latest calibration_snapshot (scope filter omitted; seed uses scope_id NULL)
-- Params: chip_id (uuid)
SELECT
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
FROM calibration_snapshot
WHERE chip_id = %(chip_id)s::uuid
  AND effective_to IS NULL
ORDER BY effective_from DESC
LIMIT 1;
