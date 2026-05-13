-- p1-step2 API-07 / Q8: calibration_run history for chip (no filters / no paging)
-- Optional time window, target_scope, paging: see q08_calibration_runs_filtered.sql
-- Params: chip_id (uuid)
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
ORDER BY start_time DESC;
