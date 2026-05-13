-- p1-step2 API-13 / Q18 (partial): simplified as_known_at — ingested_at <= t
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
  AND ingested_at <= %(t)s::timestamptz
ORDER BY effective_from DESC, computed_at DESC
LIMIT 1;
