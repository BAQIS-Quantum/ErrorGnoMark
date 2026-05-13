-- p1-step2 API-09 / Q11: calibration_snapshot valid at t (as_effective_at); optional scope omitted
-- Params: chip_id (uuid), t (timestamptz)
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
  AND effective_from <= %(t)s::timestamptz
  AND (effective_to > %(t)s::timestamptz OR effective_to IS NULL)
ORDER BY effective_from DESC
LIMIT 1;
