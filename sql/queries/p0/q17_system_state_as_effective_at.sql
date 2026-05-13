-- p1-step2 API-13 / Q17: system_state valid at t (as_effective_at)
-- Params: chip_id (uuid), t (timestamptz)
SELECT
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
FROM system_state
WHERE chip_id = %(chip_id)s::uuid
  AND effective_from <= %(t)s::timestamptz
  AND (effective_to > %(t)s::timestamptz OR effective_to IS NULL)
ORDER BY effective_from DESC
LIMIT 1;
