-- p1-step2 API-11 / Q13: metric history for subject + metric in [start, end) (no paging)
-- Q14 (same filters + LIMIT/OFFSET): see q14_metric_history_paged.sql
-- Params: subject_id (uuid), metric_definition_id (uuid), start (timestamptz), end (timestamptz)
-- Seed slice uses subject_type = qubit only.
SELECT
    observation_record_id,
    chip_id,
    subject_type,
    subject_id,
    scope_id,
    metric_definition_id,
    producer_type,
    producer_id,
    value_numeric,
    value_text,
    value_json,
    unit,
    quality_flag,
    observation_time,
    effective_from,
    effective_to,
    published_at,
    ingested_at,
    source_id,
    created_at
FROM observation_record
WHERE subject_type = 'qubit'::subject_type_enum
  AND subject_id = %(subject_id)s::uuid
  AND metric_definition_id = %(metric_definition_id)s::uuid
  AND observation_time >= %(start)s::timestamptz
  AND observation_time < %(end)s::timestamptz
ORDER BY observation_time ASC;
