-- p1-step2 API-16 / Q23: known observations with optional subject/metric + paging
-- Params: chip_id (uuid), t (timestamptz); subject_type, subject_id, metric_definition_id (nullable);
--         limit (int), offset (int)
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
  AND (%(subject_type)s IS NULL OR subject_type = %(subject_type)s::subject_type_enum)
  AND (%(subject_id)s IS NULL OR subject_id = %(subject_id)s::uuid)
  AND (%(metric_definition_id)s IS NULL OR metric_definition_id = %(metric_definition_id)s::uuid)
ORDER BY ingested_at DESC, observation_time DESC
LIMIT %(limit)s::int
OFFSET %(offset)s::int;
