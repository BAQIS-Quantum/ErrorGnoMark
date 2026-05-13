-- p1-step2 API-06 / Q7: structure_event history for chip (no paging / no time window)
-- Optional event_time window + paging: see q07_structure_events_filtered.sql
-- Params: chip_id (uuid)
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
ORDER BY event_time DESC;
