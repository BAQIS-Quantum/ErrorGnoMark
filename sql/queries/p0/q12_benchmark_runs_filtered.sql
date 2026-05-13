-- p1-step2 API-10 / Q12: benchmark_run list with optional filters + paging
-- Params: chip_id (uuid); bench_name, t_start, t_end, target_scope_id (nullable);
--         limit (int), offset (int)
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
  AND (%(bench_name)s::text IS NULL OR benchmark_name = %(bench_name)s::text)
  AND (%(t_start)s::timestamptz IS NULL OR start_time >= %(t_start)s::timestamptz)
  AND (%(t_end)s::timestamptz IS NULL OR start_time < %(t_end)s::timestamptz)
  AND (%(target_scope_id)s::uuid IS NULL OR target_scope_id = %(target_scope_id)s::uuid)
ORDER BY start_time DESC
LIMIT %(limit)s
OFFSET %(offset)s;
