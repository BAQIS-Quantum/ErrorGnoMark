-- p1-step2 API-16 / Q23: observations known at ingest time t (minimal: no subject/metric filters)
-- Params: chip_id (uuid), t (timestamptz)
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
WHERE chip_id = %(chip_id)s::uuid
  AND ingested_at <= %(t)s::timestamptz
ORDER BY ingested_at DESC, observation_time DESC
LIMIT 10;
