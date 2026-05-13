-- p1-step2 API-06 / Q7: structure_event list with optional event_time window + paging
-- Params: chip_id (uuid); t_start, t_end (timestamptz, nullable); limit (int); offset (int)
SELECT
    structure_event_id,
    chip_id,
    event_type,
    change_summary,
    changed_scope_id,
    event_time,
    effective_time,
    published_at,
    ingested_at,
    source_id
FROM structure_event
WHERE chip_id = %(chip_id)s::uuid
  AND (%(t_start)s::timestamptz IS NULL OR event_time >= %(t_start)s::timestamptz)
  AND (%(t_end)s::timestamptz IS NULL OR event_time < %(t_end)s::timestamptz)
ORDER BY event_time DESC
LIMIT %(limit)s
OFFSET %(offset)s;
