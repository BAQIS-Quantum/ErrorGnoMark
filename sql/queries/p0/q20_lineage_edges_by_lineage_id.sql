-- p1-step2 API-14 / Q19–Q21 Step 2: upstream edges for a lineage_id
-- Params: lineage_id (uuid)
SELECT
    lineage_edge_id,
    lineage_id,
    upstream_object_type,
    upstream_object_id,
    edge_role,
    created_at
FROM lineage_edge
WHERE lineage_id = %(lineage_id)s::uuid
ORDER BY edge_role NULLS LAST, created_at ASC;
