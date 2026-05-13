-- p1-step2 API-10 / Q12: benchmark_run history for chip (no filters / no paging)
-- Filtered + paged slice: see q12_benchmark_runs_filtered.sql
-- Params: chip_id (uuid)
SELECT
    benchmark_run_id,
    benchmark_name,
    benchmark_version_id,
    chip_id,
    target_scope_id,
    input_config_json,
    result_ref,
    status,
    start_time,
    end_time,
    ingested_at,
    source_id,
    created_at
FROM benchmark_run
WHERE chip_id = %(chip_id)s::uuid
ORDER BY start_time DESC;
