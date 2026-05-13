-- p1-step2 API-15 / Q22: recent ingested facts with optional time window + limit
-- Params: chip_id (uuid); start, end (timestamptz, nullable); limit (int)
SELECT *
FROM (
    SELECT
        'structure_event'::text AS object_type,
        structure_event_id AS object_id,
        ingested_at,
        jsonb_build_object(
            'event_type', event_type,
            'event_time', event_time
        ) AS summary
    FROM structure_event
    WHERE chip_id = %(chip_id)s::uuid

    UNION ALL

    SELECT
        'calibration_artifact'::text AS object_type,
        calibration_artifact_id AS object_id,
        ingested_at,
        jsonb_build_object(
            'artifact_type', artifact_type,
            'produced_at', produced_at
        ) AS summary
    FROM calibration_artifact
    WHERE chip_id = %(chip_id)s::uuid

    UNION ALL

    SELECT
        'observation_record'::text AS object_type,
        observation_record_id AS object_id,
        ingested_at,
        jsonb_build_object(
            'subject_type', subject_type,
            'metric_definition_id', metric_definition_id,
            'observation_time', observation_time
        ) AS summary
    FROM observation_record
    WHERE chip_id = %(chip_id)s::uuid
) t
WHERE (%(start)s IS NULL OR ingested_at >= %(start)s::timestamptz)
  AND (%(end)s IS NULL OR ingested_at < %(end)s::timestamptz)
ORDER BY ingested_at DESC
LIMIT %(limit)s::int;
