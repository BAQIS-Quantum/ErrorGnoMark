-- q26: Side-by-side comparison of calibration (external) vs benchmark (EGM)
--      observation records for a given chip.
-- Parameters: :chip_id, :since_time, :limit_n
--
-- The producer_type column distinguishes the two sources:
--   'calibration_artifact'  →  Quafu official calibration
--   'benchmark_run'         →  EGM internal experiment (RB / XEB / ...)

SELECT
    o.observation_time,
    o.producer_type,
    md.metric_name,
    o.value_numeric,
    o.value_json,
    o.quality_flag,
    o.subject_type,
    o.observation_record_id
FROM observation_record o
JOIN metric_definition md
    ON md.metric_definition_id = o.metric_definition_id
WHERE o.chip_id = :chip_id ::uuid
    AND o.observation_time >= :since_time ::timestamptz
ORDER BY o.observation_time DESC
LIMIT :limit_n;
