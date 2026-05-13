-- p1-step2 API-05 / Q5: latest structure_snapshot for chip (query_mode = latest)
-- Params: chip_id (uuid)
SELECT
    structure_snapshot_id,
    chip_id,
    scope_id,
    effective_from,
    effective_to,
    computed_at,
    ingested_at,
    source_id
FROM structure_snapshot
WHERE chip_id = %(chip_id)s::uuid
  AND effective_to IS NULL
ORDER BY effective_from DESC
LIMIT 1;
