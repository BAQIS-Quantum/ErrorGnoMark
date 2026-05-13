-- p1-step2 API-07 / Q8: calibration_run list with optional time window + target_scope + paging
-- Params: chip_id (uuid); t_start, t_end, target_scope_id (nullable); limit (int); offset (int)
SELECT
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
    raw_payload_ref,
    created_at
FROM calibration_run
WHERE chip_id = %(chip_id)s::uuid
  AND (%(t_start)s::timestamptz IS NULL OR start_time >= %(t_start)s::timestamptz)
  AND (%(t_end)s::timestamptz IS NULL OR start_time < %(t_end)s::timestamptz)
  AND (%(target_scope_id)s::uuid IS NULL OR target_scope_id = %(target_scope_id)s::uuid)
ORDER BY start_time DESC
LIMIT %(limit)s
OFFSET %(offset)s;
