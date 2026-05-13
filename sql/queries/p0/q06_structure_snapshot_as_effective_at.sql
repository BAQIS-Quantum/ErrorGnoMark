-- p1-step2 API-05 / Q6: structure_snapshot valid at time t (as_effective_at)
-- Params: chip_id (uuid), t (timestamptz ISO string)
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
  AND effective_from <= %(t)s::timestamptz
  AND (effective_to > %(t)s::timestamptz OR effective_to IS NULL)
ORDER BY effective_from DESC
LIMIT 1;
